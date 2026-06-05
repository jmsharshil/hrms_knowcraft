"""
Test IP address parsing to ensure port numbers are stripped correctly.
"""

def test_ip_parsing():
    """Test various IP address formats with and without ports."""
    
    test_cases = [
        # (input, expected_output)
        ("122.170.55.74:59596", "122.170.55.74"),
        ("122.170.55.74:59600", "122.170.55.74"),
        ("192.168.1.1:8080", "192.168.1.1"),
        ("10.0.0.1", "10.0.0.1"),  # No port
        ("127.0.0.1:3000", "127.0.0.1"),
        ("[::1]:8080", "::1"),  # IPv6
        ("[2001:db8::1]:443", "2001:db8::1"),  # IPv6
        ("", None),
        (None, None),
        ("169.254.130.5", "169.254.130.5"),  # Azure internal IP
    ]
    
    print("Testing IP address parsing logic:")
    print("=" * 60)
    
    all_passed = True
    for input_ip, expected in test_cases:
        # Replicate the middleware logic
        ip_address = input_ip
        
        if ip_address and ":" in ip_address:
            if ip_address.startswith("["):
                ip_address = ip_address.split("]")[0].lstrip("[")
            else:
                ip_address = ip_address.split(":")[0]
        
        ip_address = ip_address or None
        
        passed = ip_address == expected
        status = "[PASS]" if passed else "[FAIL]"
        
        if not passed:
            all_passed = False
            print(f"{status} Input: {repr(input_ip):30} Expected: {expected:20} Got: {ip_address}")
        else:
            print(f"{status} Input: {repr(input_ip):30} -> {ip_address}")
    
    print("=" * 60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_ip_parsing()
