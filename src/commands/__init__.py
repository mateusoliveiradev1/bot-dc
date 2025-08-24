# -*- coding: utf-8 -*-
"""
Comandos do Hawk Bot - Estrutura Modular
Este módulo organiza todos os comandos em Cogs separados para melhor manutenibilidade
"""

import logging
from typing import List, Tuple

logger = logging.getLogger('HawkBot.Commands')

# Lista de todos os Cogs disponíveis
AVAILABLE_COGS = [
    'src.commands.pubg_commands',
    'src.commands.music_commands', 
    'src.commands.season_commands',
    'src.commands.admin_commands'
]

# Mapeamento de categorias para facilitar o gerenciamento
COG_CATEGORIES = {
    'pubg': 'src.commands.pubg_commands',
    'music': 'src.commands.music_commands',
    'seasons': 'src.commands.season_commands', 
    'admin': 'src.commands.admin_commands'
}

# Função para carregar todos os Cogs
async def load_all_cogs(bot) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Carrega todos os Cogs disponíveis
    
    Returns:
        Tuple contendo listas de cogs carregados com sucesso e falhas
    """
    loaded_cogs = []
    failed_cogs = []
    
    logger.info(f"Iniciando carregamento de {len(AVAILABLE_COGS)} Cogs...")
    
    for cog_name in AVAILABLE_COGS:
        try:
            await bot.load_extension(cog_name)
            loaded_cogs.append(cog_name)
            logger.info(f"✅ Cog carregado: {cog_name}")
        except Exception as e:
            failed_cogs.append((cog_name, str(e)))
            logger.error(f"❌ Erro ao carregar Cog {cog_name}: {e}")
    
    logger.info(f"Carregamento concluído: {len(loaded_cogs)} sucessos, {len(failed_cogs)} falhas")
    return loaded_cogs, failed_cogs

# Função para recarregar um Cog específico
async def reload_cog(bot, cog_name: str) -> Tuple[bool, str]:
    """Recarrega um Cog específico
    
    Args:
        bot: Instância do bot
        cog_name: Nome do Cog a ser recarregado
        
    Returns:
        Tuple com status de sucesso e mensagem
    """
    try:
        await bot.reload_extension(cog_name)
        logger.info(f"Cog {cog_name} recarregado com sucesso")
        return True, f"Cog {cog_name} recarregado com sucesso"
    except Exception as e:
        logger.error(f"Erro ao recarregar Cog {cog_name}: {e}")
        return False, f"Erro ao recarregar Cog {cog_name}: {e}"

# Função para carregar Cogs por categoria
async def load_cogs_by_category(bot, categories: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Carrega Cogs específicos por categoria
    
    Args:
        bot: Instância do bot
        categories: Lista de categorias a carregar
        
    Returns:
        Tuple contendo listas de cogs carregados com sucesso e falhas
    """
    loaded_cogs = []
    failed_cogs = []
    
    for category in categories:
        if category in COG_CATEGORIES:
            cog_name = COG_CATEGORIES[category]
            try:
                await bot.load_extension(cog_name)
                loaded_cogs.append(cog_name)
                logger.info(f"✅ Cog da categoria '{category}' carregado: {cog_name}")
            except Exception as e:
                failed_cogs.append((cog_name, str(e)))
                logger.error(f"❌ Erro ao carregar Cog da categoria '{category}': {e}")
        else:
            logger.warning(f"Categoria '{category}' não encontrada")
    
    return loaded_cogs, failed_cogs

# Função para descarregar todos os Cogs
async def unload_all_cogs(bot) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Descarrega todos os Cogs carregados
    
    Returns:
        Tuple contendo listas de cogs descarregados com sucesso e falhas
    """
    unloaded_cogs = []
    failed_cogs = []
    
    for cog_name in AVAILABLE_COGS:
        try:
            await bot.unload_extension(cog_name)
            unloaded_cogs.append(cog_name)
            logger.info(f"✅ Cog descarregado: {cog_name}")
        except Exception as e:
            failed_cogs.append((cog_name, str(e)))
            logger.error(f"❌ Erro ao descarregar Cog {cog_name}: {e}")
    
    return unloaded_cogs, failed_cogs

__version__ = "1.0.0"
__author__ = "Hawk Esports Dev Team"