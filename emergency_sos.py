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
        
        # Sample hospital data for major Indian cities
        self.hospitals_data = {
            'kochi': [
                {'name': 'Ernakulam Medical Centre', 'lat': 9.9816, 'lon': 76.2999, 'phone': '0484-2371010'},
                {'name': 'Medical Trust Hospital', 'lat': 9.9558, 'lon': 76.2603, 'phone': '0484-2358001'},
                {'name': 'Amrita Institute of Medical Sciences', 'lat': 10.0104, 'lon': 76.3615, 'phone': '0484-2801234'},
                {'name': 'Government Medical College Hospital', 'lat': 9.9816, 'lon': 76.2999, 'phone': '0484-2388471'},
                {'name': 'Rajagiri Hospital', 'lat': 10.0489, 'lon': 76.3508, 'phone': '0484-2905000'}
            ],
            'delhi': [
                {'name': 'All India Institute of Medical Sciences (AIIMS)', 'lat': 28.5672, 'lon': 77.2100, 'phone': '011-26588500'},
                {'name': 'Safdarjung Hospital', 'lat': 28.5706, 'lon': 77.2066, 'phone': '011-26165060'},
                {'name': 'Ram Manohar Lohia Hospital', 'lat': 28.6264, 'lon': 77.2176, 'phone': '011-23404262'},
                {'name': 'Lady Hardinge Medical College', 'lat': 28.6358, 'lon': 77.2245, 'phone': '011-23408142'}
            ],
            'mumbai': [
                {'name': 'King Edward Memorial Hospital', 'lat': 18.9894, 'lon': 72.8320, 'phone': '022-24136051'},
                {'name': 'Tata Memorial Hospital', 'lat': 19.0111, 'lon': 72.8459, 'phone': '022-24177000'},
                {'name': 'Bombay Hospital', 'lat': 18.9681, 'lon': 72.8224, 'phone': '022-22067676'},
                {'name': 'Hinduja Hospital', 'lat': 19.0330, 'lon': 72.8397, 'phone': '022-24447000'}
            ],
            'bengaluru': [
                {'name': 'Bangalore Medical College and Research Institute', 'lat': 12.9716, 'lon': 77.5946, 'phone': '080-26702000'},
                {'name': 'St. Johns Medical College Hospital', 'lat': 12.9279, 'lon': 77.6271, 'phone': '080-49467000'},
                {'name': 'Manipal Hospital', 'lat': 12.9698, 'lon': 77.7499, 'phone': '080-25022446'},
                {'name': 'Apollo Hospital', 'lat': 12.9698, 'lon': 77.7499, 'phone': '080-26304050'}
            ]
        }
    
    def get_emergency_contacts(self):
        """Get list of emergency contacts"""
        return self.emergency_contacts
    
    def get_nearest_hospitals_map(self, city_name):
        """Generate a map showing nearest hospitals"""
        city_lower = city_name.lower()
        
        # Get hospitals for the city
        hospitals = self.hospitals_data.get(city_lower, [])
        
        if not hospitals:
            # Default to Kochi if city not found
            hospitals = self.hospitals_data['kochi']
            center_lat, center_lon = 9.9816, 76.2999
        else:
            # Calculate center point
            center_lat = sum(h['lat'] for h in hospitals) / len(hospitals)
            center_lon = sum(h['lon'] for h in hospitals) / len(hospitals)
        
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
        city_lower = city_name.lower()
        hospitals = self.hospitals_data.get(city_lower, self.hospitals_data['kochi'])
        
        hospital_list = []
        for hospital in hospitals:
            hospital_info = f"{hospital['name']} - {hospital['phone']}"
            hospital_list.append(hospital_info)
        
        return hospital_list
    
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
