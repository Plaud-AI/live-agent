"""
Global AI Components Manager

This module manages the lifecycle of heavyweight AI components (VAD, STT, LLM, TTS).
These components are initialized once at application startup and shared across all sessions.

Components are expensive to create (model loading, network connections) but cheap to use.
Each WebSocket connection gets the global components and creates per-session state.

Example:
    # At application startup
    components = await Components.initialize(config)
    
    # In WebSocket handler
    vad_stream = components.vad.stream()  # Create per-session VAD stream
    transcript = await components.stt.transcribe(audio)  # Use global STT
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from config.models import Config
from core.vad.base import VAD
from core.stt.base import STT
from core.llm.base import LLM
from core.tts.base import TTS


"""
TODO: Memory component needs to be added
"""

@dataclass
class Components:
    """
    Container for all initialized AI components.
    
    Attributes:
        vad: Voice Activity Detection component
        stt: Speech-to-Text component
        llm: Large Language Model component
        tts: Text-to-Speech component
    """
    vad: VAD
    stt: STT
    llm: LLM
    tts: TTS
    
    @classmethod
    async def initialize(cls, config: Config) -> Components:
        """
        Initialize all AI components from configuration.
        
        This method loads models and initializes API clients. Components that
        don't depend on each other are loaded in parallel to minimize startup time.
        
        Args:
            config: Application configuration (validated by Pydantic)
            
        Returns:
            Initialized Components instance
            
        Raises:
            ValueError: If any component configuration is invalid
            RuntimeError: If any component fails to initialize
            
        Example:
            config = load_config("config.yaml")
            components = await Components.initialize(config)
        """
        logging.info("Initializing AI components...")
        start_time = asyncio.get_event_loop().time()
        
        # Import factory functions here to avoid circular imports
        import core.vad.base as vad
        import core.stt.base as stt
        import core.llm.base as llm
        import core.tts.base as tts
        
        try:
            # Phase 1: Initialize independent components in parallel
            # These don't depend on each other, so we can load simultaneously
            logging.info("Phase 1: Loading VAD, STT, LLM in parallel...")
            
            vad_task = asyncio.create_task(
                vad.create_from_config(config.components.vad),
                name="init_vad"
            )
            stt_task = asyncio.create_task(
                stt.create_from_config(config.components.stt),
                name="init_stt"
            )
            llm_task = asyncio.create_task(
                llm.create_from_config(config.components.llm),
                name="init_llm"
            )
            tts_task = asyncio.create_task(
                tts.create_from_config(config.components.tts, config.audio_params),
                name="init_tts"
            )
            
            # Wait for all to complete (will raise on first failure - fast fail)
            vad, stt, llm, tts = await asyncio.gather(vad_task, stt_task, llm_task, tts_task)
            
            elapsed = asyncio.get_event_loop().time() - start_time
            logging.info(f"✅ All components initialized successfully in {elapsed:.2f}s")
            
            return cls(vad=vad, stt=stt, llm=llm, tts=tts)
            
        except Exception as e:
            logging.critical(f"❌ Component initialization failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize components: {e}") from e
    
    async def aclose(self) -> None:
        """
        Cleanup all components on application shutdown.
        
        Components are closed in reverse order of initialization to handle
        any dependencies gracefully.
        """
        logging.info("Shutting down AI components...")
        
        # Close in reverse order: TTS → LLM → STT → VAD
        for name, component in [
            ("TTS", self.tts),
            ("LLM", self.llm),
            ("STT", self.stt),
            ("VAD", self.vad)
        ]:
            if hasattr(component, 'aclose'):
                try:
                    await component.aclose()
                    logging.info(f"✓ {name} closed")
                except Exception as e:
                    logging.warning(f"Error closing {name}: {e}")
        
        logging.info("All components shut down")
