def format_indian_currency(amount: float) -> str:
    """Format currency in Indian numbering system (Lakhs/Crores)"""
    if amount == 0:
        return "₹0"
    
    # Convert to string and split at decimal
    amount_str = f"{amount:.2f}"
    integer_part, decimal_part = amount_str.split('.')
    
    # Reverse the integer part for easier processing
    reversed_int = integer_part[::-1]
    
    # Add commas - first comma after 3 digits, then every 2 digits
    formatted = ""
    for i, digit in enumerate(reversed_int):
        if i == 3:  # First comma after 3 digits
            formatted = "," + formatted
        elif i > 3 and (i - 3) % 2 == 0:  # Then every 2 digits
            formatted = "," + formatted
        formatted = digit + formatted
    
    return f"₹{formatted}.{decimal_part}"

def get_state_coordinates():
    """Get approximate center coordinates for Indian states"""
    return {
        "Andhra Pradesh": {"lat": 15.9129, "lon": 79.7400},
        "Arunachal Pradesh": {"lat": 28.2180, "lon": 94.7278},
        "Assam": {"lat": 26.2006, "lon": 92.9376},
        "Bihar": {"lat": 25.0961, "lon": 85.3131},
        "Chhattisgarh": {"lat": 21.2787, "lon": 81.8661},
        "Delhi": {"lat": 28.7041, "lon": 77.1025},
        "Goa": {"lat": 15.2993, "lon": 74.1240},
        "Gujarat": {"lat": 23.0225, "lon": 72.5714},
        "Haryana": {"lat": 29.0588, "lon": 76.0856},
        "Himachal Pradesh": {"lat": 31.1048, "lon": 77.1734},
        "Jharkhand": {"lat": 23.6102, "lon": 85.2799},
        "Karnataka": {"lat": 15.3173, "lon": 75.7139},
        "Kerala": {"lat": 10.8505, "lon": 76.2711},
        "Madhya Pradesh": {"lat": 22.9734, "lon": 78.6569},
        "Maharashtra": {"lat": 19.7515, "lon": 75.7139},
        "Manipur": {"lat": 24.6637, "lon": 93.9063},
        "Meghalaya": {"lat": 25.4670, "lon": 91.3662},
        "Mizoram": {"lat": 23.1645, "lon": 92.9376},
        "Nagaland": {"lat": 26.1584, "lon": 94.5624},
        "Odisha": {"lat": 20.9517, "lon": 85.0985},
        "Punjab": {"lat": 31.1471, "lon": 75.3412},
        "Rajasthan": {"lat": 27.0238, "lon": 74.2179},
        "Sikkim": {"lat": 27.5330, "lon": 88.5122},
        "Tamil Nadu": {"lat": 11.1271, "lon": 78.6569},
        "Telangana": {"lat": 18.1124, "lon": 79.0193},
        "Tripura": {"lat": 23.9408, "lon": 91.9882},
        "Uttar Pradesh": {"lat": 26.8467, "lon": 80.9462},
        "Uttarakhand": {"lat": 30.0668, "lon": 79.0193},
        "West Bengal": {"lat": 22.9868, "lon": 87.8550},
        "Andaman and Nicobar Islands": {"lat": 11.7401, "lon": 92.6586},
        "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
        "Dadra and Nagar Haveli and Daman and Diu": {"lat": 20.1809, "lon": 73.0169},
        "Jammu and Kashmir": {"lat": 34.0837, "lon": 74.7973},
        "Ladakh": {"lat": 34.1526, "lon": 77.5770},
        "Lakshadweep": {"lat": 10.5667, "lon": 72.6417},
        "Puducherry": {"lat": 11.9416, "lon": 79.8083}
    }