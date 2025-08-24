import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from enum import Enum

class SessionType(Enum):
    SCRIM = "scrim"
    RANKED = "ranked"
    MM = "mm"
    TOURNAMENT = "tournament"

class CheckInStatus(Enum):
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    NO_SHOW = "no_show"

class CheckInSystem:
    def __init__(self, bot, storage):
        self.bot = bot
        self.storage = storage
        self.active_sessions = {}
        self.checkin_data = self._load_checkin_data()
    
    def _load_checkin_data(self) -> Dict[str, Any]:
        """Carrega dados de check-in do armazenamento"""
        if "checkin_system" not in self.storage.data:
            self.storage.data["checkin_system"] = {
                "sessions": {},
                "player_stats": {},
                "settings": {
                    "reminder_time": 30,  # minutos antes da sessão
                    "auto_checkout_time": 180,  # minutos após o fim da sessão
                    "require_checkout": True
                }
            }
            self.storage.save_data()
        return self.storage.data["checkin_system"]
    
    def create_session(self, session_id: str, session_type: SessionType, 
                      start_time: datetime, end_time: datetime, 
                      max_players: int = None, description: str = "") -> Dict[str, Any]:
        """Cria uma nova sessão de check-in"""
        session = {
            "id": session_id,
            "type": session_type.value,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "max_players": max_players,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "players": {},
            "checkin_count": 0,
            "checkout_count": 0
        }
        
        self.checkin_data["sessions"][session_id] = session
        self.active_sessions[session_id] = session
        self.storage.save_data()
        
        return session
    
    def check_in_player(self, session_id: str, user_id: str, username: str) -> Dict[str, Any]:
        """Registra check-in de um jogador"""
        if session_id not in self.checkin_data["sessions"]:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        session = self.checkin_data["sessions"][session_id]
        
        # Verifica se a sessão ainda está ativa
        if session["status"] != "active":
            raise ValueError("Sessão não está ativa")
        
        # Verifica limite de jogadores
        if session["max_players"] and session["checkin_count"] >= session["max_players"]:
            raise ValueError("Sessão lotada")
        
        # Verifica se já fez check-in
        if user_id in session["players"]:
            if session["players"][user_id]["status"] == CheckInStatus.CHECKED_IN.value:
                raise ValueError("Jogador já fez check-in")
        
        # Registra check-in
        checkin_time = datetime.now()
        session["players"][user_id] = {
            "username": username,
            "checkin_time": checkin_time.isoformat(),
            "checkout_time": None,
            "status": CheckInStatus.CHECKED_IN.value
        }
        
        session["checkin_count"] += 1
        
        # Atualiza estatísticas do jogador
        self._update_player_stats(user_id, username, "checkin", session["type"])
        
        self.storage.save_data()
        
        return {
            "success": True,
            "checkin_time": checkin_time,
            "position": session["checkin_count"],
            "session": session
        }
    
    def check_out_player(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Registra check-out de um jogador"""
        if session_id not in self.checkin_data["sessions"]:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        session = self.checkin_data["sessions"][session_id]
        
        # Verifica se o jogador fez check-in
        if user_id not in session["players"]:
            raise ValueError("Jogador não fez check-in nesta sessão")
        
        player_data = session["players"][user_id]
        
        # Verifica se já fez check-out
        if player_data["status"] == CheckInStatus.CHECKED_OUT.value:
            raise ValueError("Jogador já fez check-out")
        
        # Registra check-out
        checkout_time = datetime.now()
        player_data["checkout_time"] = checkout_time.isoformat()
        player_data["status"] = CheckInStatus.CHECKED_OUT.value
        
        session["checkout_count"] += 1
        
        # Atualiza estatísticas do jogador
        self._update_player_stats(user_id, player_data["username"], "checkout", session["type"])
        
        self.storage.save_data()
        
        return {
            "success": True,
            "checkout_time": checkout_time,
            "session": session
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de uma sessão"""
        return self.checkin_data["sessions"].get(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Retorna todas as sessões ativas"""
        active = []
        for session in self.checkin_data["sessions"].values():
            if session["status"] == "active":
                active.append(session)
        return active
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """Fecha uma sessão"""
        if session_id not in self.checkin_data["sessions"]:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        session = self.checkin_data["sessions"][session_id]
        session["status"] = "closed"
        session["closed_at"] = datetime.now().isoformat()
        
        # Remove da lista de sessões ativas
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        self.storage.save_data()
        
        return session
    
    def get_player_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna sessões de um jogador"""
        player_sessions = []
        
        for session in self.checkin_data["sessions"].values():
            if user_id in session["players"]:
                session_data = session.copy()
                session_data["player_data"] = session["players"][user_id]
                player_sessions.append(session_data)
        
        # Ordena por data de criação (mais recente primeiro)
        player_sessions.sort(key=lambda x: x["created_at"], reverse=True)
        
        return player_sessions[:limit]
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancela uma sessão"""
        if session_id not in self.checkin_data["sessions"]:
            return False
            
        session = self.checkin_data["sessions"][session_id]
        
        # Só pode cancelar sessões ativas
        if session["status"] != "active":
            return False
            
        # Atualizar status
        session["status"] = "cancelled"
        session["cancelled_at"] = datetime.now().isoformat()
        
        # Remove da lista de sessões ativas
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Salvar alterações
        self.storage.save_data()
        
        return True
        
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Obtém todas as sessões ordenadas por data de criação"""
        all_sessions = list(self.checkin_data["sessions"].values())
        
        # Ordenar por data de criação (mais recentes primeiro)
        all_sessions.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return all_sessions
    
    def get_player_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de um jogador"""
        return self.checkin_data["player_stats"].get(user_id, {
            "total_checkins": 0,
            "total_checkouts": 0,
            "no_shows": 0,
            "by_type": {
                "scrim": {"checkins": 0, "checkouts": 0},
                "ranked": {"checkins": 0, "checkouts": 0},
                "mm": {"checkins": 0, "checkouts": 0},
                "tournament": {"checkins": 0, "checkouts": 0}
            },
            "last_activity": None
        })
    
    def _update_player_stats(self, user_id: str, username: str, action: str, session_type: str):
        """Atualiza estatísticas do jogador"""
        if user_id not in self.checkin_data["player_stats"]:
            self.checkin_data["player_stats"][user_id] = {
                "username": username,
                "total_checkins": 0,
                "total_checkouts": 0,
                "no_shows": 0,
                "by_type": {
                    "scrim": {"checkins": 0, "checkouts": 0},
                    "ranked": {"checkins": 0, "checkouts": 0},
                    "mm": {"checkins": 0, "checkouts": 0},
                    "tournament": {"checkins": 0, "checkouts": 0}
                },
                "last_activity": None
            }
        
        stats = self.checkin_data["player_stats"][user_id]
        stats["username"] = username  # Atualiza username
        stats["last_activity"] = datetime.now().isoformat()
        
        if action == "checkin":
            stats["total_checkins"] += 1
            stats["by_type"][session_type]["checkins"] += 1
        elif action == "checkout":
            stats["total_checkouts"] += 1
            stats["by_type"][session_type]["checkouts"] += 1
    
    def mark_no_show(self, session_id: str, user_id: str):
        """Marca jogador como faltoso"""
        if session_id not in self.checkin_data["sessions"]:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        session = self.checkin_data["sessions"][session_id]
        
        if user_id in session["players"]:
            session["players"][user_id]["status"] = CheckInStatus.NO_SHOW.value
            
            # Atualiza estatísticas
            if user_id in self.checkin_data["player_stats"]:
                self.checkin_data["player_stats"][user_id]["no_shows"] += 1
        
        self.storage.save_data()
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Retorna resumo de uma sessão"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        summary = {
            "session_info": {
                "id": session["id"],
                "type": session["type"],
                "description": session["description"],
                "status": session["status"],
                "start_time": session["start_time"],
                "end_time": session["end_time"]
            },
            "stats": {
                "total_players": len(session["players"]),
                "checked_in": session["checkin_count"],
                "checked_out": session["checkout_count"],
                "no_shows": len([p for p in session["players"].values() if p["status"] == CheckInStatus.NO_SHOW.value])
            },
            "players": session["players"]
        }
        
        return summary