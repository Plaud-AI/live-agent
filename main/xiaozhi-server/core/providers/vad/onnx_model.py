"""
ONNX Model Wrapper for Silero VAD

Provides ONNX inference session management and RNN state handling.
"""

import atexit
import os
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import onnxruntime  # type: ignore

_resource_files = ExitStack()
atexit.register(_resource_files.close)


SUPPORTED_SAMPLE_RATES = [8000, 16000]


def _get_onnx_model_path() -> str:
    """
    Get the path to the Silero VAD ONNX model file.
    
    Returns:
        Path to the ONNX model file
    """
    # Try to get from package resources first
    try:
        import importlib.resources
        res = importlib.resources.files("core.providers.vad.resources") / "silero_vad.onnx"
        ctx = importlib.resources.as_file(res)
        path = str(_resource_files.enter_context(ctx))
        return path
    except Exception:
        # Fallback to relative path
        current_dir = Path(__file__).parent
        model_path = current_dir / "resources" / "silero_vad.onnx"
        if model_path.exists():
            return str(model_path)
        raise FileNotFoundError(
            f"Silero VAD ONNX model not found. Please ensure silero_vad.onnx "
            f"exists in {current_dir / 'resources'}"
        )


def new_inference_session(force_cpu: bool = True) -> onnxruntime.InferenceSession:
    """
    Create a new ONNX Runtime inference session.
    
    Args:
        force_cpu: If True, force CPU execution provider
    
    Returns:
        ONNX Runtime InferenceSession
    """
    model_path = _get_onnx_model_path()
    
    opts = onnxruntime.SessionOptions()
    opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
    opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
    
    if force_cpu and "CPUExecutionProvider" in onnxruntime.get_available_providers():
        session = onnxruntime.InferenceSession(
            model_path, providers=["CPUExecutionProvider"], sess_options=opts
        )
    else:
        session = onnxruntime.InferenceSession(model_path, sess_options=opts)
    
    return session


class OnnxModel:
    """
    ONNX Model wrapper for Silero VAD with RNN state management.
    
    This class manages the RNN state and context between inference calls,
    which is crucial for accurate VAD detection.
    """
    
    def __init__(self, *, onnx_session: onnxruntime.InferenceSession, sample_rate: int) -> None:
        """
        Initialize OnnxModel.
        
        Args:
            onnx_session: ONNX Runtime inference session
            sample_rate: Sample rate for inference (8000 or 16000)
        """
        self._sess = onnx_session
        self._sample_rate = sample_rate
        
        if sample_rate not in SUPPORTED_SAMPLE_RATES:
            raise ValueError("Silero VAD only supports 8KHz and 16KHz sample rates")
        
        if sample_rate == 8000:
            self._window_size_samples = 256
            self._context_size = 32
        elif sample_rate == 16000:
            self._window_size_samples = 512
            self._context_size = 64
        
        self._sample_rate_nd = np.array(sample_rate, dtype=np.int64)
        self._context = np.zeros((1, self._context_size), dtype=np.float32)
        self._rnn_state = np.zeros((2, 1, 128), dtype=np.float32)
        self._input_buffer = np.zeros(
            (1, self._context_size + self._window_size_samples), dtype=np.float32
        )
    
    @property
    def sample_rate(self) -> int:
        """Get the sample rate"""
        return self._sample_rate
    
    @property
    def window_size_samples(self) -> int:
        """Get the window size in samples"""
        return self._window_size_samples
    
    @property
    def context_size(self) -> int:
        """Get the context size in samples"""
        return self._context_size
    
    def __call__(self, x: np.ndarray) -> float:
        """
        Run inference on audio data.
        
        This method:
        1. Combines previous context with new input
        2. Runs ONNX inference with RNN state
        3. Updates context and state for next call
        
        Args:
            x: Audio data array of shape (window_size_samples,)
        
        Returns:
            Speech probability [0, 1]
        """
        # Combine context and new input
        self._input_buffer[:, : self._context_size] = self._context
        self._input_buffer[:, self._context_size :] = x
        
        # Run inference with RNN state
        ort_inputs = {
            "input": self._input_buffer,
            "state": self._rnn_state,
            "sr": self._sample_rate_nd,
        }
        out, self._state = self._sess.run(None, ort_inputs)
        
        # Update context for next inference
        self._context = self._input_buffer[:, -self._context_size :]  # type: ignore
        return out.item()  # type: ignore

