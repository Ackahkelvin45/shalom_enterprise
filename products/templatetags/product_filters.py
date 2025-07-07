from django import template

register = template.Library()
@register.filter
def get_type(value):
    """Returns the type of the value"""
    return type(value).__name__



@register.filter
def get_item(value, key):
    """Safely get an item from a dictionary or return 0"""
    if not isinstance(value, dict):
        return 0
        
    try:
        # Try with the key as-is first
        if key in value:
            return value[key]
            
        # Try converting key to match dictionary key type
        dict_keys = value.keys()
        if dict_keys:
            # Get the type of the first key
            key_type = type(next(iter(dict_keys)))
            
            try:
                # Convert the input key to match the dictionary key type
                converted_key = key_type(key)
                return value.get(converted_key, 0)
            except (ValueError, TypeError):
                pass
                
        return 0
    except Exception:
        return 0