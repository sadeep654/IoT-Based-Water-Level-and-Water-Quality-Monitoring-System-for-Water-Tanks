<!-- Repository Banner -->
<p align="center">
  <img src="img/banner.png" width="100%" alt="Project Banner" />
</p>

---

## 🔹 Overview  

This system automates the monitoring of water tanks by collecting data from multiple sensors and displaying it through a web dashboard. It alerts the user when the tank is too low or full, and automatically controls the pump based on predefined thresholds. In addition to level detection, the system evaluates water quality using pH and turbidity measurements.
>See the demo video below for a quick visual explanation of how the system works.
<p align="center">
  <img src="img/demo.gif" alt="water" width="1000px">
</p>
 
>Full system description referenced from project documentation.

---

## 🔹 Objectives  

- Enable real-time remote monitoring of water level and water quality  
- Reduce water wastage by automating pump operations  
- Prevent pump dry-running and overflow  
- Provide user-friendly alerts and control options  
- Support domestic and small-scale industrial water systems  

---

## 🔹 Architecture

<p align="center">
  <img src="img/diagram.png" width="100%" alt="water" />
</p>

>**Architecture Summary**
>### **Core Modules**
- **Water Level Module:** Ultrasonic sensor + controller unit  
- **Water Quality Module:** pH and turbidity sensors  
- **Communication Module:** Wi-Fi (NodeMCU) and optional GSM alerts  
- **Control Module:** Automatic pump control + manual override  
- **Visualization Module:** Web/mobile dashboard for live data  

>### **How It Works**
1. Water level and quality sensors collect data continuously  
2. Microcontrollers process the measurements  
3. Data is transmitted to a cloud dashboard  
4. Tank status and water quality values are displayed in real time  
5. Alerts are issued for high/low water levels or poor water quality  
6. Pump is automatically switched on/off based on level thresholds  

---

## 🔹 Hardware Components  

- Arduino Uno / Arduino Nano  
- NodeMCU ESP8266  
- Ultrasonic Sensor (HC-SR04)  
- pH Sensor  
- Turbidity Sensor  
- GSM Module (optional)  
- LCD Display (16×2, I2C)  
- Buzzer, LEDs, buttons  
- LM2596 Buck Converter  
- Power supply: 5V regulated  

---

---

## 🔹 Testing Approach  

- Verified each sensor independently (pH, turbidity, ultrasonic)  
- Tested Wi-Fi connectivity, cloud data flow, and dashboard interface  
- Performed five trials per water source sample  
- Compared measurements with physical/manual readings  
- Monitored full system performance for reliability and response time  

---

## 🔹 Key Features  

>### **Water Level Monitoring**
- Ultrasonic sensor for accurate distance measurement  
- Alerts for low, medium, and full tank status  
- Automatic pump cutoff at full level  
- Dry-run protection when water is low  

>### **Water Quality Monitoring**
- pH sensor for acidity/alkalinity  
- Turbidity sensor for water clarity  
- Optional dissolved oxygen readings  

>### **Connectivity & Alerts**
- Wi-Fi for real-time updates  
- GSM alerts for critical conditions  
- Web dashboard to view water status and pump state  

---

## 🔹 Software Tools  

- Arduino IDE  
- Visual Studio Code  
- Blynk / Firebase / Custom Web App  
- Google Sheets (optional logging)  
- Android Studio (optional mobile app)

---

## 🔹 Future Improvements  

- Add temperature, TDS, and conductivity sensors  
- Implement AI/ML-based water quality prediction  
- Integrate into full smart-home automation  
- Build a dedicated mobile application  
- Cloud IoT dashboard with analytics  

---

## 🔹 License & Citation 
```bash
This project is released under the MIT License.  
See the `LICENSE` file for full license details.
```
- **If you use this work in any form—academic, research, educational, or practical—please cite it as:**
```bash
Kasthuriarachchi, S.D. & Perera, H.A.K.D., 2022. IoT Water Level and Water Quality Monitoring System. [Online] Available at: https://github.com/sadeep654/IoT-Water-Monitoring-System (Accessed: date-you-accessed).
```

---

## 🧑‍💻 Authors  

>- **Kasthuriarachchi, S.D.**  
>- **Perera H.A.K.D.**
