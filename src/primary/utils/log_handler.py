import re
import logging

class WebUrlFilter(logging.Filter):
    """Filter out web URLs from log messages"""
    
    def filter(self, record):
        if not hasattr(record, 'msg'):
            return True
            
        if isinstance(record.msg, str):
            # Filter out web interface messages
            if "Web interface available at http://" in record.msg:
                return False
                
            # Redact URLs if they need to appear in logs
            record.msg = re.sub(
                r'(http|https)://[^\s<>"]+',
                '[REDACTED URL]',
                record.msg
            )
        
        return True

# Add this filter to the existing loggers
def apply_log_filters():
    """Apply web URL filters to all loggers"""
    web_filter = WebUrlFilter()
    
    # Apply to root logger
    for handler in logging.root.handlers:
        handler.addFilter(web_filter)
    
    # Apply to newtarr logger
    newtarr_logger = logging.getLogger('newtarr')
    for handler in newtarr_logger.handlers:
        handler.addFilter(web_filter)
