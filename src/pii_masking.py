import re
import logging
from typing import Any, Dict, List, Optional

try:
    from utils import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class PIIMasking:
    
    LEVEL_FULL = "full"
    LEVEL_PARTIAL = "partial"
    LEVEL_SHOW_LAST = "show_last"
    
    SENSITIVE_FIELDS = {
        'customer_name': 'name',
        'postal_code': 'postal_code',
        'phone': 'phone',
        'email': 'email',
        'credit_card': 'credit_card',
        'ssn': 'ssn',
        'sales': 'financial',
        'profit': 'financial',
        'shipping_cost': 'financial',
        'discount': 'financial'
    }
    
    @staticmethod
    def mask_name(name: str, level: str = LEVEL_PARTIAL) -> str:
        if not name or not isinstance(name, str):
            return "***"
        
        name = name.strip()
        if not name:
            return "***"
        
        if level == PIIMasking.LEVEL_FULL:
            return "****"
        
        parts = name.split()
        
        if level == PIIMasking.LEVEL_SHOW_LAST:
            if len(parts) >= 2:
                return f"{parts[0][0]}*** {parts[-1]}"
            return f"{parts[0][0]}***"
        
        masked_parts = []
        for part in parts:
            if len(part) > 1:
                masked_parts.append(f"{part[0]}{'*' * (len(part) - 1)}")
            else:
                masked_parts.append(part)
        
        return " ".join(masked_parts)
    
    @staticmethod
    def mask_postal_code(postal_code: str, show_digits: int = 3) -> str:
        if not postal_code or not isinstance(postal_code, str):
            return "*****"
        
        postal_code = postal_code.strip()
        if not postal_code:
            return "*****"
        
        if len(postal_code) <= show_digits:
            return "*" * len(postal_code)
        
        return postal_code[:show_digits] + "*" * (len(postal_code) - show_digits)
    
    @staticmethod
    def mask_phone(phone: str, show_last: int = 4) -> str:
        if not phone or not isinstance(phone, str):
            return "***-***-****"
        
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) <= show_last:
            return "*" * len(digits)
        
        masked = "*" * (len(digits) - show_last) + digits[-show_last:]
        
        return masked
    
    @staticmethod
    def mask_email(email: str) -> str:
        if not email or not isinstance(email, str):
            return "***@***"
        
        email = email.strip()
        
        if '@' not in email:
            return "***"
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 1)
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_credit_card(card: str, show_last: int = 4) -> str:
        if not card or not isinstance(card, str):
            return "****-****-****-****"
        
        digits = re.sub(r'\D', '', card)
        
        if len(digits) < show_last:
            return "*" * len(digits)
        
        masked = "*" * (len(digits) - show_last) + digits[-show_last:]
        
        if len(masked) == 16:
            return f"{masked[:4]}-{masked[4:8]}-{masked[8:12]}-{masked[12:16]}"
        
        return masked
    
    @staticmethod
    def mask_ssn(ssn: str, show_last: int = 4) -> str:
        if not ssn or not isinstance(ssn, str):
            return "***-**-****"
        
        digits = re.sub(r'\D', '', ssn)
        
        if len(digits) < show_last:
            return "*" * len(digits)
        
        masked = "*" * (len(digits) - show_last) + digits[-show_last:]
        
        if len(masked) == 11:
            return f"{masked[:3]}-{masked[3:5]}-{masked[5:9]}"
        
        return masked
    
    @staticmethod
    def mask_financial(amount: Any, show_last: int = 2) -> str:
        try:
            amount_str = str(amount).strip()
            
            if '.' in amount_str:
                integer_part, decimal_part = amount_str.split('.')
                integer_digits = re.sub(r'\D', '', integer_part)
                
                if len(integer_digits) > show_last:
                    masked_int = "*" * (len(integer_digits) - show_last) + integer_digits[-show_last:]
                else:
                    masked_int = integer_digits
                
                return f"{masked_int}.{decimal_part}"
            else:
                digits = re.sub(r'\D', '', amount_str)
                if len(digits) > show_last:
                    return "*" * (len(digits) - show_last) + digits[-show_last:]
                return digits
        
        except Exception as e:
            logger.warning(f"Error masking financial data: {e}")
            return "****"
    
    @staticmethod
    def mask_dataframe(df, field_mappings: Optional[Dict[str, str]] = None):
        try:
            import pandas as pd
            df = df.copy()
            
            if field_mappings is None:
                field_mappings = {}
            
            for column, mask_type in field_mappings.items():
                if column not in df.columns:
                    logger.warning(f"Column '{column}' not found in DataFrame")
                    continue
                
                if mask_type == 'name':
                    df[column] = df[column].apply(PIIMasking.mask_name)
                elif mask_type == 'postal_code':
                    df[column] = df[column].apply(PIIMasking.mask_postal_code)
                elif mask_type == 'phone':
                    df[column] = df[column].apply(PIIMasking.mask_phone)
                elif mask_type == 'email':
                    df[column] = df[column].apply(PIIMasking.mask_email)
                elif mask_type == 'credit_card':
                    df[column] = df[column].apply(PIIMasking.mask_credit_card)
                elif mask_type == 'ssn':
                    df[column] = df[column].apply(PIIMasking.mask_ssn)
                elif mask_type == 'financial':
                    df[column] = df[column].apply(PIIMasking.mask_financial)
                else:
                    logger.warning(f"Unknown mask type: {mask_type}")
            
            logger.info(f"Masked {len(field_mappings)} columns in DataFrame")
            return df
        
        except ImportError:
            logger.error("pandas not available for DataFrame masking")
            return df
    
    @staticmethod
    def mask_dict(data: Dict[str, Any], field_mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        masked_data = data.copy()
        
        if field_mappings is None:
            field_mappings = {}
        
        for key, mask_type in field_mappings.items():
            if key not in masked_data:
                continue
            
            value = masked_data[key]
            
            if mask_type == 'name':
                masked_data[key] = PIIMasking.mask_name(value)
            elif mask_type == 'postal_code':
                masked_data[key] = PIIMasking.mask_postal_code(value)
            elif mask_type == 'phone':
                masked_data[key] = PIIMasking.mask_phone(value)
            elif mask_type == 'email':
                masked_data[key] = PIIMasking.mask_email(value)
            elif mask_type == 'credit_card':
                masked_data[key] = PIIMasking.mask_credit_card(value)
            elif mask_type == 'ssn':
                masked_data[key] = PIIMasking.mask_ssn(value)
            elif mask_type == 'financial':
                masked_data[key] = PIIMasking.mask_financial(value)
        
        return masked_data
    
    @staticmethod
    def get_default_mappings_for_table(table_name: str) -> Dict[str, str]:
        default_mappings = {
            'customer': {
                'customer_name': 'name',
                'postal_code': 'postal_code'
            },
            'order_product': {
                'sales': 'financial',
                'profit': 'financial',
                'shipping_cost': 'financial',
                'discount': 'financial'
            },
            'order': {},
            'return': {},
            'product': {},
            'category': {},
            'subcategory': {},
            'segment': {}
        }
        
        return default_mappings.get(table_name, {})

def mask_customer_name(name: str) -> str:
    return PIIMasking.mask_name(name)


def mask_postal_code(postal_code: str) -> str:
    return PIIMasking.mask_postal_code(postal_code)


def mask_financial(amount: Any) -> str:
    return PIIMasking.mask_financial(amount)


if __name__ == "__main__":
    print("PII Masking Examples:")
    print(f"Name: John Doe -> {PIIMasking.mask_name('John Doe')}")
    print(f"Postal Code: 12345 -> {PIIMasking.mask_postal_code('12345')}")
    print(f"Phone: 555-123-4567 -> {PIIMasking.mask_phone('555-123-4567')}")
    print(f"Email: john.doe@example.com -> {PIIMasking.mask_email('john.doe@example.com')}")
    print(f"Credit Card: 4532015112830366 -> {PIIMasking.mask_credit_card('4532015112830366')}")
    print(f"SSN: 123-45-6789 -> {PIIMasking.mask_ssn('123-45-6789')}")
    print(f"Financial: 1234.56 -> {PIIMasking.mask_financial(1234.56)}")



