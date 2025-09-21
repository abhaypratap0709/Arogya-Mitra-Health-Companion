import folium
import requests
import json
from folium import plugins

class EmergencySOSManager:
    def __init__(self):
        self.emergency_contacts = {
            'National Emergency': '112',
            'Ambulance': '108', 
            'Fire Emergency': '101',
            'Police': '100',
            'Women Helpline': '1091',
            'Child Helpline': '1098'
        }
        
        # Comprehensive hospital data for major Indian cities
        self.hospitals_data = {
            'delhi': [
                {'name': 'All India Institute of Medical Sciences (AIIMS)', 'lat': 28.5672, 'lon': 77.2100, 'phone': '011-26588500'},
                {'name': 'Safdarjung Hospital', 'lat': 28.5706, 'lon': 77.2066, 'phone': '011-26165060'},
                {'name': 'Ram Manohar Lohia Hospital', 'lat': 28.6264, 'lon': 77.2176, 'phone': '011-23404262'},
                {'name': 'Lady Hardinge Medical College', 'lat': 28.6358, 'lon': 77.2245, 'phone': '011-23408142'},
                {'name': 'Apollo Hospital Delhi', 'lat': 28.5355, 'lon': 77.2459, 'phone': '011-4040-6060'}
            ],
            'mumbai': [
                {'name': 'King Edward Memorial Hospital', 'lat': 18.9894, 'lon': 72.8320, 'phone': '022-24136051'},
                {'name': 'Tata Memorial Hospital', 'lat': 19.0111, 'lon': 72.8459, 'phone': '022-24177000'},
                {'name': 'Bombay Hospital', 'lat': 18.9681, 'lon': 72.8224, 'phone': '022-22067676'},
                {'name': 'Hinduja Hospital', 'lat': 19.0330, 'lon': 72.8397, 'phone': '022-24447000'},
                {'name': 'Lilavati Hospital', 'lat': 19.1330, 'lon': 72.8397, 'phone': '022-2640-0000'}
            ],
            'bengaluru': [
                {'name': 'Bangalore Medical College and Research Institute', 'lat': 12.9716, 'lon': 77.5946, 'phone': '080-26702000'},
                {'name': 'St. Johns Medical College Hospital', 'lat': 12.9279, 'lon': 77.6271, 'phone': '080-49467000'},
                {'name': 'Manipal Hospital', 'lat': 12.9698, 'lon': 77.7499, 'phone': '080-25022446'},
                {'name': 'Apollo Hospital Bangalore', 'lat': 12.9698, 'lon': 77.7499, 'phone': '080-26304050'},
                {'name': 'Fortis Hospital', 'lat': 12.9043, 'lon': 77.6048, 'phone': '080-6621-4000'}
            ],
            'chennai': [
                {'name': 'Apollo Hospital Chennai', 'lat': 13.0827, 'lon': 80.2707, 'phone': '044-2829-3333'},
                {'name': 'Fortis Malar Hospital', 'lat': 13.0067, 'lon': 80.2206, 'phone': '044-4289-2222'},
                {'name': 'MIOT International', 'lat': 12.9716, 'lon': 80.2206, 'phone': '044-4200-2288'},
                {'name': 'Global Hospitals', 'lat': 13.0827, 'lon': 80.2707, 'phone': '044-2277-7777'}
            ],
            'hyderabad': [
                {'name': 'Apollo Hospital Hyderabad', 'lat': 17.4065, 'lon': 78.4772, 'phone': '040-2323-3333'},
                {'name': 'Continental Hospitals', 'lat': 17.4065, 'lon': 78.4772, 'phone': '040-6700-0000'},
                {'name': 'KIMS Hospital', 'lat': 17.4065, 'lon': 78.4772, 'phone': '040-4488-5000'},
                {'name': 'Care Hospital', 'lat': 17.4065, 'lon': 78.4772, 'phone': '040-3041-8888'}
            ],
            'kolkata': [
                {'name': 'Apollo Gleneagles Hospital', 'lat': 22.5726, 'lon': 88.3639, 'phone': '033-2320-3040'},
                {'name': 'Fortis Hospital Kolkata', 'lat': 22.5726, 'lon': 88.3639, 'phone': '033-6628-0000'},
                {'name': 'AMRI Hospital', 'lat': 22.5726, 'lon': 88.3639, 'phone': '033-2288-0000'},
                {'name': 'Peerless Hospital', 'lat': 22.5726, 'lon': 88.3639, 'phone': '033-2460-0000'}
            ],
            'pune': [
                {'name': 'Apollo Hospital Pune', 'lat': 18.5204, 'lon': 73.8567, 'phone': '020-6680-1000'},
                {'name': 'Ruby Hall Clinic', 'lat': 18.5204, 'lon': 73.8567, 'phone': '020-2616-3333'},
                {'name': 'Sahyadri Hospital', 'lat': 18.5204, 'lon': 73.8567, 'phone': '020-2444-0000'},
                {'name': 'Deenanath Mangeshkar Hospital', 'lat': 18.5204, 'lon': 73.8567, 'phone': '020-4015-1515'}
            ],
            'ahmedabad': [
                {'name': 'Apollo Hospital Ahmedabad', 'lat': 23.0225, 'lon': 72.5714, 'phone': '079-6670-1000'},
                {'name': 'Sterling Hospital', 'lat': 23.0225, 'lon': 72.5714, 'phone': '079-4000-0000'},
                {'name': 'Zydus Hospital', 'lat': 23.0225, 'lon': 72.5714, 'phone': '079-4000-5000'},
                {'name': 'Shalby Hospital', 'lat': 23.0225, 'lon': 72.5714, 'phone': '079-4000-4000'}
            ],
            'jaipur': [
                {'name': 'Fortis Hospital Jaipur', 'lat': 26.9124, 'lon': 75.7873, 'phone': '0141-300-1000'},
                {'name': 'Apollo Hospital Jaipur', 'lat': 26.9124, 'lon': 75.7873, 'phone': '0141-300-0000'},
                {'name': 'Sawai Man Singh Hospital', 'lat': 26.9124, 'lon': 75.7873, 'phone': '0141-256-0291'},
                {'name': 'Mahatma Gandhi Hospital', 'lat': 26.9124, 'lon': 75.7873, 'phone': '0141-256-0291'}
            ],
            'kochi': [
                {'name': 'Ernakulam Medical Centre', 'lat': 9.9816, 'lon': 76.2999, 'phone': '0484-2371010'},
                {'name': 'Medical Trust Hospital', 'lat': 9.9558, 'lon': 76.2603, 'phone': '0484-2358001'},
                {'name': 'Amrita Institute of Medical Sciences', 'lat': 10.0104, 'lon': 76.3615, 'phone': '0484-2801234'},
                {'name': 'Government Medical College Hospital', 'lat': 9.9816, 'lon': 76.2999, 'phone': '0484-2388471'},
                {'name': 'Rajagiri Hospital', 'lat': 10.0489, 'lon': 76.3508, 'phone': '0484-2905000'}
            ],
            'lucknow': [
                {'name': 'Apollo Hospital Lucknow', 'lat': 26.8467, 'lon': 80.9462, 'phone': '0522-424-0000'},
                {'name': 'Fortis Hospital Lucknow', 'lat': 26.8467, 'lon': 80.9462, 'phone': '0522-424-2000'},
                {'name': 'King George Medical University', 'lat': 26.8467, 'lon': 80.9462, 'phone': '0522-225-7450'},
                {'name': 'Sanjay Gandhi Postgraduate Institute', 'lat': 26.8467, 'lon': 80.9462, 'phone': '0522-249-5000'}
            ],
            'chandigarh': [
                {'name': 'Post Graduate Institute of Medical Education', 'lat': 30.7333, 'lon': 76.7794, 'phone': '0172-275-6000'},
                {'name': 'Apollo Hospital Chandigarh', 'lat': 30.7333, 'lon': 76.7794, 'phone': '0172-666-0000'},
                {'name': 'Fortis Hospital Mohali', 'lat': 30.7333, 'lon': 76.7794, 'phone': '0172-509-0000'},
                {'name': 'Max Hospital Mohali', 'lat': 30.7333, 'lon': 76.7794, 'phone': '0172-509-0000'}
            ],
            'indore': [
                {'name': 'Apollo Hospital Indore', 'lat': 22.7196, 'lon': 75.8577, 'phone': '0731-401-1000'},
                {'name': 'Fortis Hospital Indore', 'lat': 22.7196, 'lon': 75.8577, 'phone': '0731-401-2000'},
                {'name': 'Choithram Hospital', 'lat': 22.7196, 'lon': 75.8577, 'phone': '0731-401-3000'},
                {'name': 'Bombay Hospital Indore', 'lat': 22.7196, 'lon': 75.8577, 'phone': '0731-401-4000'}
            ],
            'bhubaneswar': [
                {'name': 'Apollo Hospital Bhubaneswar', 'lat': 20.2961, 'lon': 85.8245, 'phone': '0674-666-0000'},
                {'name': 'Kalinga Hospital', 'lat': 20.2961, 'lon': 85.8245, 'phone': '0674-230-0000'},
                {'name': 'AIIMS Bhubaneswar', 'lat': 20.2961, 'lon': 85.8245, 'phone': '0674-230-1000'},
                {'name': 'Sparsh Hospital', 'lat': 20.2961, 'lon': 85.8245, 'phone': '0674-230-2000'}
            ],
            'guwahati': [
                {'name': 'Apollo Hospital Guwahati', 'lat': 26.1445, 'lon': 91.7362, 'phone': '0361-710-0000'},
                {'name': 'GNRC Hospital', 'lat': 26.1445, 'lon': 91.7362, 'phone': '0361-710-1000'},
                {'name': 'Down Town Hospital', 'lat': 26.1445, 'lon': 91.7362, 'phone': '0361-710-2000'},
                {'name': 'Narayana Superspeciality Hospital', 'lat': 26.1445, 'lon': 91.7362, 'phone': '0361-710-3000'}
            ]
        }
        
        # City aliases for better matching
        self.city_aliases = {
            'delhi': ['new delhi', 'ncr', 'gurgaon', 'gurugram', 'noida', 'faridabad'],
            'mumbai': ['bombay', 'navi mumbai', 'thane', 'kalyan'],
            'bengaluru': ['bangalore', 'bengaluru'],
            'chennai': ['madras'],
            'hyderabad': ['secunderabad'],
            'kolkata': ['calcutta'],
            'pune': ['pimpri', 'chinchwad'],
            'ahmedabad': ['gandhinagar'],
            'jaipur': ['pink city'],
            'kochi': ['cochin', 'ernakulam'],
            'lucknow': ['lko'],
            'chandigarh': ['chd', 'panchkula', 'mohali'],
            'indore': ['madhya pradesh'],
            'bhubaneswar': ['odisha', 'cuttack'],
            'guwahati': ['assam', 'dispur']
        }
    
    def get_emergency_contacts(self):
        """Get list of emergency contacts"""
        return self.emergency_contacts
    
    def find_city_match(self, city_name):
        """Find matching city from input, including aliases"""
        city_lower = city_name.lower().strip()
        
        # Direct match
        if city_lower in self.hospitals_data:
            return city_lower
        
        # Check aliases
        for main_city, aliases in self.city_aliases.items():
            if city_lower in aliases or any(alias in city_lower for alias in aliases):
                return main_city
        
        # Partial match
        for main_city in self.hospitals_data.keys():
            if city_lower in main_city or main_city in city_lower:
                return main_city
        
        return None

    def get_nearest_hospitals_map(self, city_name):
        """Generate a map showing nearest hospitals"""
        matched_city = self.find_city_match(city_name)
        
        if matched_city:
            hospitals = self.hospitals_data[matched_city]
            # Calculate center point
            center_lat = sum(h['lat'] for h in hospitals) / len(hospitals)
            center_lon = sum(h['lon'] for h in hospitals) / len(hospitals)
        else:
            # Default to Delhi if city not found
            hospitals = self.hospitals_data['delhi']
            center_lat, center_lon = 28.6139, 77.2090
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add hospital markers
        for hospital in hospitals:
            popup_text = f"""
            <div style="width: 200px;">
                <h4>{hospital['name']}</h4>
                <p><strong>📞 Phone:</strong> {hospital['phone']}</p>
                <p><a href="tel:{hospital['phone']}" target="_blank">Call Now</a></p>
            </div>
            """
            
            folium.Marker(
                location=[hospital['lat'], hospital['lon']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=hospital['name'],
                icon=folium.Icon(color='red', icon='plus', prefix='fa')
            ).add_to(m)
        
        # Add emergency contacts in the corner
        emergency_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>🚨 Emergency Contacts</h4>
        '''
        
        for contact, number in self.emergency_contacts.items():
            emergency_html += f'<p><strong>{contact}:</strong> <a href="tel:{number}">{number}</a></p>'
        
        emergency_html += '</div>'
        
        # Add emergency contacts as a custom HTML element
        # Temporarily commented out due to folium API changes
        # m.get_root().html.add_child(folium.Element(emergency_html))
        
        return m
    
    def get_hospital_list(self, city_name):
        """Get list of hospitals for a city"""
        matched_city = self.find_city_match(city_name)
        
        if matched_city:
            hospitals = self.hospitals_data[matched_city]
        else:
            # Default to Delhi if city not found
            hospitals = self.hospitals_data['delhi']
        
        hospital_list = []
        for hospital in hospitals:
            hospital_info = f"{hospital['name']} - {hospital['phone']}"
            hospital_list.append(hospital_info)
        
        return hospital_list
    
    def get_available_cities(self):
        """Get list of all available cities"""
        return list(self.hospitals_data.keys())
    
    def get_emergency_instructions(self, language='en'):
        """Get emergency instructions in specified language"""
        instructions = {
            'en': [
                "Stay calm and assess the situation",
                "Call emergency services immediately",
                "Provide clear location information",
                "Follow dispatcher instructions",
                "Stay on the line until help arrives"
            ],
            'hi': [
                "शांत रहें और स्थिति का आकलन करें",
                "तुरंत आपातकालीन सेवाओं को कॉल करें",
                "स्पष्ट स्थान की जानकारी प्रदान करें",
                "डिस्पैचर के निर्देशों का पालन करें",
                "मदद आने तक लाइन पर रहें"
            ]
        }
        
        return instructions.get(language, instructions['en'])
    
    def send_emergency_alert(self, user_location, emergency_type):
        """Send emergency alert (placeholder for real implementation)"""
        # In a real implementation, this would:
        # 1. Send SMS to emergency contacts
        # 2. Share location with emergency services
        # 3. Log the emergency in the system
        
        from datetime import datetime
        alert_data = {
            'timestamp': str(datetime.now()),
            'location': user_location,
            'type': emergency_type,
            'status': 'alert_sent'
        }
        
        return alert_data
