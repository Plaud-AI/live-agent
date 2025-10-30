"""
ExpFilter - Exponential Filter Utility

Simple exponential moving average filter for smoothing values.
"""


class ExpFilter:
    """
    Exponential filter for smoothing values.
    
    Used to smooth noisy signals by applying exponential moving average.
    """
    
    def __init__(self, alpha: float, max_val: float = -1.0) -> None:
        """
        Initialize ExpFilter.
        
        Args:
            alpha: Smoothing factor (0-1). Higher values = less smoothing.
            max_val: Optional maximum value to clamp the filtered result.
        """
        self._alpha = alpha
        self._filtered = -1.0
        self._max_val = max_val
    
    def reset(self, alpha: float = -1.0) -> None:
        """Reset the filter state"""
        if alpha != -1.0:
            self._alpha = alpha
        self._filtered = -1.0
    
    def apply(self, exp: float, sample: float) -> float:
        """
        Apply exponential filter to a sample.
        
        Args:
            exp: Exponent factor (typically 1.0)
            sample: New sample value
        
        Returns:
            Filtered value
        """
        if self._filtered == -1.0:
            self._filtered = sample
        else:
            a = self._alpha**exp
            self._filtered = a * self._filtered + (1 - a) * sample
        
        if self._max_val != -1.0 and self._filtered > self._max_val:
            self._filtered = self._max_val
        
        return self._filtered
    
    def filtered(self) -> float:
        """Get the current filtered value"""
        return self._filtered
    
    def update_base(self, alpha: float) -> None:
        """Update the alpha parameter"""
        self._alpha = alpha

