"""
PCB Component Library — Standard Electronic Component Footprints & 3D Dimensions

Provides real-world component dimensions for:
1. Generating accurate 3D CadQuery representations of PCBs
2. Feeding into AI prompts so Claude can place components correctly
3. Creating matching enclosure cutouts (USB ports, buttons, LEDs, etc.)

All dimensions in mm. Footprint names follow KiCad conventions.
"""

from typing import Dict, Any, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
# Each component has:
#   category      — grouping (MCU, Connector, Passive, etc.)
#   name          — human-readable name
#   footprint     — KiCad footprint name
#   body          — 3D body dimensions {x, y, z} in mm
#   pins          — pin count
#   pitch         — pin pitch in mm
#   pad_size      — {x, y} pad dimensions
#   thermal_pad   — optional exposed pad for heat dissipation
#   mounting      — "smd" | "through_hole"
#   keepout       — minimum clearance around component
#   connectors    — for connector types, the mating dimensions (for enclosure cutouts)
# ═══════════════════════════════════════════════════════════════════════════════

COMPONENTS: Dict[str, Dict[str, Any]] = {

    # ─── Microcontrollers ─────────────────────────────────────────────────
    "esp32_wroom": {
        "category": "MCU",
        "name": "ESP32-WROOM-32",
        "footprint": "RF_Module:ESP32-WROOM-32",
        "body": {"x": 18.0, "y": 25.5, "z": 3.1},
        "pins": 38,
        "pitch": 1.27,
        "mounting": "smd",
        "keepout": 2.0,
        "has_antenna": True,
        "antenna_keepout": {"x": 18.0, "y": 6.0},  # no copper under antenna area
        "notes": "WiFi+BT module. Keep antenna area clear of ground plane.",
    },
    "esp32_s3": {
        "category": "MCU",
        "name": "ESP32-S3-WROOM-1",
        "footprint": "RF_Module:ESP32-S3-WROOM-1",
        "body": {"x": 18.0, "y": 25.5, "z": 3.2},
        "pins": 44,
        "pitch": 1.27,
        "mounting": "smd",
        "keepout": 2.0,
        "has_antenna": True,
        "antenna_keepout": {"x": 18.0, "y": 6.0},
        "notes": "WiFi+BT with USB OTG. AI/ML capable.",
    },
    "atmega328p_tqfp": {
        "category": "MCU",
        "name": "ATmega328P (TQFP-32)",
        "footprint": "Package_QFP:TQFP-32_7x7mm_P0.8mm",
        "body": {"x": 7.0, "y": 7.0, "z": 1.2},
        "pins": 32,
        "pitch": 0.8,
        "mounting": "smd",
        "keepout": 1.0,
        "notes": "Arduino Uno MCU. 8-bit AVR, 32KB flash.",
    },
    "atmega328p_dip": {
        "category": "MCU",
        "name": "ATmega328P (DIP-28)",
        "footprint": "Package_DIP:DIP-28_W7.62mm",
        "body": {"x": 7.62, "y": 35.56, "z": 4.0},
        "pins": 28,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Through-hole Arduino MCU. Good for prototyping.",
    },
    "stm32f103_tqfp48": {
        "category": "MCU",
        "name": "STM32F103C8T6 (TQFP-48)",
        "footprint": "Package_QFP:TQFP-48_7x7mm_P0.5mm",
        "body": {"x": 7.0, "y": 7.0, "z": 1.2},
        "pins": 48,
        "pitch": 0.5,
        "mounting": "smd",
        "keepout": 1.0,
        "notes": "Blue Pill MCU. ARM Cortex-M3, 72MHz.",
    },
    "rp2040": {
        "category": "MCU",
        "name": "RP2040",
        "footprint": "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm",
        "body": {"x": 7.0, "y": 7.0, "z": 0.9},
        "pins": 56,
        "pitch": 0.4,
        "mounting": "smd",
        "keepout": 1.0,
        "thermal_pad": {"x": 3.2, "y": 3.2},
        "notes": "Raspberry Pi Pico MCU. Dual-core ARM Cortex-M0+.",
    },
    "raspberry_pi_pico": {
        "category": "MCU_Module",
        "name": "Raspberry Pi Pico",
        "footprint": "Module:RaspberryPi_Pico",
        "body": {"x": 21.0, "y": 51.0, "z": 3.7},
        "pins": 40,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Complete module with RP2040, USB-C, and flash.",
    },
    "arduino_nano": {
        "category": "MCU_Module",
        "name": "Arduino Nano",
        "footprint": "Module:Arduino_Nano",
        "body": {"x": 18.0, "y": 45.0, "z": 5.0},
        "pins": 30,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "connectors": {"usb_mini": {"x": 7.6, "y": 5.0, "z": 3.6}},
        "notes": "Complete ATmega328P module with USB.",
    },

    # ─── Connectors ───────────────────────────────────────────────────────
    "usb_c_16pin": {
        "category": "Connector",
        "name": "USB Type-C (16-pin)",
        "footprint": "Connector_USB:USB_C_Receptacle_GCT_USB4105",
        "body": {"x": 8.94, "y": 7.35, "z": 3.26},
        "pins": 16,
        "pitch": 0.5,
        "mounting": "smd",
        "keepout": 1.5,
        "mating_face": {"x": 8.94, "y": 3.26},  # cutout needed in enclosure
        "edge_mount": True,
        "notes": "Board-edge USB-C receptacle. Place flush with PCB edge.",
    },
    "usb_micro_b": {
        "category": "Connector",
        "name": "USB Micro-B",
        "footprint": "Connector_USB:USB_Micro-B_Molex_47346-0001",
        "body": {"x": 7.5, "y": 5.6, "z": 2.8},
        "pins": 5,
        "pitch": 0.65,
        "mounting": "smd",
        "keepout": 1.5,
        "mating_face": {"x": 7.5, "y": 2.8},
        "edge_mount": True,
        "notes": "Common micro USB connector.",
    },
    "usb_a_female": {
        "category": "Connector",
        "name": "USB A Female",
        "footprint": "Connector_USB:USB_A_CNCTech_1001-011-01101",
        "body": {"x": 14.0, "y": 13.1, "z": 5.7},
        "pins": 4,
        "pitch": 2.0,
        "mounting": "through_hole",
        "keepout": 1.5,
        "mating_face": {"x": 12.0, "y": 4.5},
        "edge_mount": True,
        "notes": "USB A host connector.",
    },
    "barrel_jack_2_1mm": {
        "category": "Connector",
        "name": "DC Barrel Jack 2.1mm",
        "footprint": "Connector_BarrelJack:BarrelJack_CUI_PJ-063AH",
        "body": {"x": 9.0, "y": 14.0, "z": 11.0},
        "pins": 3,
        "pitch": 5.0,
        "mounting": "through_hole",
        "keepout": 2.0,
        "mating_face": {"diameter": 8.0, "depth": 11.0},
        "edge_mount": True,
        "notes": "5.5/2.1mm barrel jack for power input.",
    },
    "jst_ph_2pin": {
        "category": "Connector",
        "name": "JST PH 2-Pin",
        "footprint": "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
        "body": {"x": 6.0, "y": 4.5, "z": 6.0},
        "pins": 2,
        "pitch": 2.0,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Battery connector. Common for LiPo cells.",
    },
    "header_2x20": {
        "category": "Connector",
        "name": "2x20 Pin Header",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
        "body": {"x": 50.8, "y": 5.08, "z": 8.5},
        "pins": 40,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Raspberry Pi GPIO header.",
    },
    "header_1x6": {
        "category": "Connector",
        "name": "1x6 Pin Header",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
        "body": {"x": 15.24, "y": 2.54, "z": 8.5},
        "pins": 6,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "UART/SPI header.",
    },
    "audio_jack_3_5mm": {
        "category": "Connector",
        "name": "3.5mm Audio Jack",
        "footprint": "Connector_Audio:Jack_3.5mm_CUI_SJ-3523-SMT",
        "body": {"x": 5.0, "y": 12.0, "z": 5.0},
        "pins": 3,
        "pitch": 2.0,
        "mounting": "smd",
        "keepout": 1.5,
        "mating_face": {"diameter": 6.0},
        "edge_mount": True,
        "notes": "TRS 3.5mm headphone/audio jack.",
    },
    "sd_card_slot": {
        "category": "Connector",
        "name": "Micro SD Card Slot",
        "footprint": "Connector_Card:microSD_HC_Molex_104031-0811",
        "body": {"x": 14.0, "y": 15.0, "z": 1.85},
        "pins": 8,
        "pitch": 1.1,
        "mounting": "smd",
        "keepout": 1.0,
        "mating_face": {"x": 11.0, "y": 1.0},
        "notes": "Push-push micro SD card slot.",
    },

    # ─── Power Management ─────────────────────────────────────────────────
    "ams1117_3v3": {
        "category": "Power",
        "name": "AMS1117-3.3V LDO",
        "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        "body": {"x": 6.5, "y": 3.5, "z": 1.6},
        "pins": 4,
        "pitch": 2.3,
        "mounting": "smd",
        "keepout": 1.0,
        "notes": "3.3V 1A LDO regulator. Needs input/output caps.",
    },
    "mp1584_module": {
        "category": "Power",
        "name": "MP1584 Buck Module",
        "footprint": "Module:MP1584_DC-DC_Buck",
        "body": {"x": 22.0, "y": 17.0, "z": 4.0},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Adjustable 3A step-down module. 4.5-28V → 0.8-20V.",
    },
    "tp4056_module": {
        "category": "Power",
        "name": "TP4056 LiPo Charger",
        "footprint": "Module:TP4056_Charger",
        "body": {"x": 26.0, "y": 17.0, "z": 4.0},
        "pins": 6,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "connectors": {"usb_micro": {"x": 7.5, "y": 2.8}},
        "notes": "LiPo charger + protection. USB micro input.",
    },
    "18650_holder": {
        "category": "Power",
        "name": "18650 Battery Holder",
        "footprint": "Battery:BatteryHolder_Keystone_1042_1x18650",
        "body": {"x": 20.5, "y": 77.0, "z": 19.0},
        "pins": 2,
        "pitch": 60.0,
        "mounting": "through_hole",
        "keepout": 3.0,
        "notes": "Single 18650 cell holder. 3.7V typical.",
    },
    "cr2032_holder": {
        "category": "Power",
        "name": "CR2032 Coin Cell Holder",
        "footprint": "Battery:BatteryHolder_Keystone_3000_1x20mm",
        "body": {"x": 24.0, "y": 24.0, "z": 5.4},
        "pins": 2,
        "pitch": 20.0,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "CR2032 3V coin cell. ~225mAh.",
    },

    # ─── Sensors ──────────────────────────────────────────────────────────
    "bme280": {
        "category": "Sensor",
        "name": "BME280 (Temp/Humidity/Pressure)",
        "footprint": "Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_ClockwisePinNumbering",
        "body": {"x": 2.5, "y": 2.5, "z": 0.93},
        "pins": 8,
        "pitch": 0.65,
        "mounting": "smd",
        "keepout": 0.5,
        "notes": "Environmental sensor. I2C/SPI. Needs vent hole in enclosure.",
    },
    "mpu6050": {
        "category": "Sensor",
        "name": "MPU-6050 (Accel/Gyro)",
        "footprint": "Package_LGA:InvenSense_QFN-24_4x4mm_P0.5mm",
        "body": {"x": 4.0, "y": 4.0, "z": 0.9},
        "pins": 24,
        "pitch": 0.5,
        "mounting": "smd",
        "keepout": 0.5,
        "notes": "6-axis IMU. I2C. Place near center of mass.",
    },
    "hc_sr04": {
        "category": "Sensor",
        "name": "HC-SR04 Ultrasonic",
        "footprint": "Sensor:HC-SR04",
        "body": {"x": 45.0, "y": 20.0, "z": 15.0},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 3.0,
        "connectors": {"transducers": {"diameter": 16.0, "spacing": 26.0}},
        "notes": "Ultrasonic distance sensor. Two 16mm transducer cylinders on front face.",
    },
    "dht22": {
        "category": "Sensor",
        "name": "DHT22 Temp/Humidity",
        "footprint": "Sensor:Aosong_DHT22",
        "body": {"x": 15.1, "y": 25.1, "z": 7.7},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Temp/humidity sensor. Needs airflow opening in enclosure.",
    },
    "pir_sensor": {
        "category": "Sensor",
        "name": "PIR Motion Sensor (HC-SR501)",
        "footprint": "Sensor:HC-SR501_PIR",
        "body": {"x": 32.0, "y": 24.0, "z": 18.0},
        "pins": 3,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 3.0,
        "connectors": {"lens": {"diameter": 23.0}},
        "notes": "PIR motion detector with Fresnel lens dome. Needs window in enclosure.",
    },

    # ─── Display ──────────────────────────────────────────────────────────
    "oled_ssd1306_128x64": {
        "category": "Display",
        "name": "OLED 0.96\" 128x64 (SSD1306)",
        "footprint": "Display:OLED_0.96in_128x64_I2C",
        "body": {"x": 27.3, "y": 27.8, "z": 3.7},
        "display_area": {"x": 21.7, "y": 11.2},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Small I2C OLED. Needs rectangular window in enclosure.",
    },
    "lcd_1602_i2c": {
        "category": "Display",
        "name": "LCD 16x2 with I2C Backpack",
        "footprint": "Display:LCD_1602_I2C",
        "body": {"x": 80.0, "y": 36.0, "z": 12.0},
        "display_area": {"x": 64.5, "y": 16.0},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Classic 2-line LCD. I2C backpack on rear.",
    },
    "tft_st7789_240x240": {
        "category": "Display",
        "name": "TFT 1.3\" 240x240 (ST7789)",
        "footprint": "Display:TFT_1.3in_240x240_SPI",
        "body": {"x": 30.0, "y": 37.0, "z": 3.2},
        "display_area": {"x": 24.0, "y": 24.0},
        "pins": 7,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Color TFT display. SPI interface.",
    },

    # ─── LEDs ─────────────────────────────────────────────────────────────
    "led_0805": {
        "category": "LED",
        "name": "SMD LED 0805",
        "footprint": "LED_SMD:LED_0805_2012Metric",
        "body": {"x": 2.0, "y": 1.25, "z": 0.8},
        "pins": 2,
        "pitch": 1.8,
        "mounting": "smd",
        "keepout": 0.3,
        "notes": "Standard SMD indicator LED.",
    },
    "led_5mm": {
        "category": "LED",
        "name": "5mm Through-Hole LED",
        "footprint": "LED_THT:LED_D5.0mm",
        "body": {"x": 5.0, "y": 5.0, "z": 8.6},
        "pins": 2,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 0.5,
        "notes": "Standard 5mm LED. Needs hole in enclosure.",
    },
    "ws2812b": {
        "category": "LED",
        "name": "WS2812B RGB LED (NeoPixel)",
        "footprint": "LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm",
        "body": {"x": 5.0, "y": 5.0, "z": 1.6},
        "pins": 4,
        "pitch": 3.2,
        "mounting": "smd",
        "keepout": 0.5,
        "notes": "Addressable RGB LED. Chainable. Needs light pipe or window.",
    },

    # ─── Buttons & Switches ──────────────────────────────────────────────
    "tactile_6x6mm": {
        "category": "Switch",
        "name": "Tactile Button 6x6mm",
        "footprint": "Button_Switch_SMD:SW_SPST_B3U-1000P",
        "body": {"x": 6.0, "y": 6.0, "z": 4.3},
        "actuator": {"diameter": 3.5, "height": 1.5},
        "pins": 4,
        "pitch": 4.5,
        "mounting": "smd",
        "keepout": 0.5,
        "notes": "Standard tact switch. Needs button cap or enclosure cutout.",
    },
    "slide_switch": {
        "category": "Switch",
        "name": "Slide Switch SPDT",
        "footprint": "Button_Switch_THT:SW_Slide_1P2T_CK_OS102011MA1QN1",
        "body": {"x": 8.5, "y": 3.5, "z": 3.5},
        "actuator": {"x": 2.0, "y": 1.5, "travel": 3.0},
        "pins": 3,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Power/mode switch. Needs slot in enclosure.",
    },
    "rotary_encoder": {
        "category": "Switch",
        "name": "Rotary Encoder with Push Button",
        "footprint": "Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm",
        "body": {"x": 12.0, "y": 12.0, "z": 20.0},
        "shaft": {"diameter": 6.0, "height": 15.0},
        "pins": 5,
        "pitch": 2.5,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Rotary knob with click. Shaft protrudes through enclosure.",
    },

    # ─── Passive Components ──────────────────────────────────────────────
    "resistor_0805": {
        "category": "Passive",
        "name": "Resistor 0805",
        "footprint": "Resistor_SMD:R_0805_2012Metric",
        "body": {"x": 2.0, "y": 1.25, "z": 0.6},
        "pins": 2,
        "pitch": 1.8,
        "mounting": "smd",
        "keepout": 0.2,
        "notes": "Standard 1/8W SMD resistor.",
    },
    "capacitor_0805": {
        "category": "Passive",
        "name": "Capacitor 0805",
        "footprint": "Capacitor_SMD:C_0805_2012Metric",
        "body": {"x": 2.0, "y": 1.25, "z": 0.8},
        "pins": 2,
        "pitch": 1.8,
        "mounting": "smd",
        "keepout": 0.2,
        "notes": "Standard MLCC ceramic capacitor.",
    },
    "capacitor_electrolytic_8mm": {
        "category": "Passive",
        "name": "Electrolytic Capacitor 8mm",
        "footprint": "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
        "body": {"x": 8.0, "y": 8.0, "z": 12.0},
        "pins": 2,
        "pitch": 3.5,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Polarized electrolytic cap. Check height clearance.",
    },
    "crystal_hc49": {
        "category": "Passive",
        "name": "Crystal HC49 (e.g., 16MHz)",
        "footprint": "Crystal:Crystal_HC49-4H_Vertical",
        "body": {"x": 11.0, "y": 4.7, "z": 13.5},
        "pins": 2,
        "pitch": 4.88,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Standard crystal oscillator.",
    },

    # ─── Communication Modules ───────────────────────────────────────────
    "nrf24l01_module": {
        "category": "RF",
        "name": "nRF24L01+ Module",
        "footprint": "Module:nRF24L01_Module",
        "body": {"x": 15.0, "y": 29.0, "z": 5.0},
        "pins": 8,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "has_antenna": True,
        "notes": "2.4GHz RF module with PCB antenna.",
    },
    "sim800l": {
        "category": "RF",
        "name": "SIM800L GSM Module",
        "footprint": "Module:SIM800L",
        "body": {"x": 22.0, "y": 18.0, "z": 3.5},
        "pins": 12,
        "pitch": 2.0,
        "mounting": "smd",
        "keepout": 2.0,
        "connectors": {"antenna": {"type": "u.fl"}},
        "notes": "GSM/GPRS cellular module. Needs external antenna.",
    },
    "gps_neo6m": {
        "category": "RF",
        "name": "NEO-6M GPS Module",
        "footprint": "Module:u-blox_NEO-6M",
        "body": {"x": 25.0, "y": 25.0, "z": 4.0},
        "pins": 4,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "has_antenna": True,
        "notes": "GPS receiver with ceramic patch antenna.",
    },

    # ─── Motor / Actuator Drivers ────────────────────────────────────────
    "drv8825": {
        "category": "Motor",
        "name": "DRV8825 Stepper Driver",
        "footprint": "Module:Pololu_Breakout_DRV8825",
        "body": {"x": 15.2, "y": 20.3, "z": 10.0},
        "pins": 16,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Stepper motor driver. Needs heatsink (included in z height).",
    },
    "l298n_module": {
        "category": "Motor",
        "name": "L298N Motor Driver Module",
        "footprint": "Module:L298N_DualH-Bridge",
        "body": {"x": 43.0, "y": 43.0, "z": 27.0},
        "pins": 15,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 3.0,
        "notes": "Dual H-bridge DC motor driver. Has heatsink.",
    },
    "servo_sg90_connector": {
        "category": "Motor",
        "name": "Servo Connector (SG90)",
        "footprint": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "body": {"x": 7.62, "y": 2.54, "z": 8.5},
        "pins": 3,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "3-pin servo header (Signal, VCC, GND).",
    },

    # ─── Audio ────────────────────────────────────────────────────────────
    "buzzer_12mm": {
        "category": "Audio",
        "name": "Piezo Buzzer 12mm",
        "footprint": "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
        "body": {"x": 12.0, "y": 12.0, "z": 9.5},
        "pins": 2,
        "pitch": 7.6,
        "mounting": "through_hole",
        "keepout": 1.0,
        "notes": "Active piezo buzzer. Needs sound hole in enclosure.",
    },
    "speaker_28mm": {
        "category": "Audio",
        "name": "Speaker 28mm",
        "footprint": "Acoustic:Speaker_28mm",
        "body": {"x": 28.0, "y": 28.0, "z": 6.0},
        "pins": 2,
        "pitch": 20.0,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "Small speaker. Needs grille opening in enclosure.",
    },

    # ─── Misc ─────────────────────────────────────────────────────────────
    "relay_5v": {
        "category": "Relay",
        "name": "SRD-05VDC Relay",
        "footprint": "Relay_THT:Relay_SPDT_Finder_36.11",
        "body": {"x": 19.0, "y": 15.3, "z": 15.5},
        "pins": 5,
        "pitch": 2.54,
        "mounting": "through_hole",
        "keepout": 2.0,
        "notes": "5V SPDT relay. 10A switching capacity.",
    },
    "screw_terminal_2pin": {
        "category": "Connector",
        "name": "Screw Terminal 2-Pin 5.08mm",
        "footprint": "TerminalBlock:TerminalBlock_bornier-2_P5.08mm",
        "body": {"x": 10.16, "y": 7.5, "z": 10.0},
        "pins": 2,
        "pitch": 5.08,
        "mounting": "through_hole",
        "keepout": 1.5,
        "notes": "Power/signal screw terminal.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# STANDARD PCB SPECS
# ═══════════════════════════════════════════════════════════════════════════════

PCB_SPECS = {
    "standard": {
        "thickness": 1.6,
        "copper_weight": "1oz",
        "copper_thickness": 0.035,
        "solder_mask_thickness": 0.02,
        "silkscreen_thickness": 0.01,
        "min_trace_width": 0.2,
        "min_clearance": 0.2,
        "min_drill": 0.3,
        "min_annular_ring": 0.15,
        "colors": {
            "substrate": "#1a472a",   # FR4 green
            "mask_green": "#1a7a1a",
            "mask_blue": "#1a1a7a",
            "mask_red": "#7a1a1a",
            "mask_black": "#1a1a1a",
            "mask_white": "#e0e0e0",
            "mask_purple": "#4a1a6a",
            "copper": "#c87533",
            "gold_finish": "#d4af37",
            "hasl_finish": "#c0c0c0",
            "silkscreen": "#ffffff",
        },
    },
    "flex": {
        "thickness": 0.2,
        "copper_weight": "0.5oz",
        "min_trace_width": 0.1,
        "min_clearance": 0.1,
        "notes": "Flexible polyimide substrate.",
    },
    "aluminum": {
        "thickness": 1.6,
        "copper_weight": "1oz",
        "notes": "Metal-core PCB for LED/power. Better thermal dissipation.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# STANDARD BOARD SHAPES & MOUNTING
# ═══════════════════════════════════════════════════════════════════════════════

BOARD_PRESETS = {
    "arduino_uno": {
        "name": "Arduino Uno Shield",
        "width": 68.6, "height": 53.3,
        "mounting_holes": [
            {"x": 14.0, "y": 2.54, "diameter": 3.2},
            {"x": 15.24, "y": 50.8, "diameter": 3.2},
            {"x": 66.04, "y": 7.62, "diameter": 3.2},
            {"x": 66.04, "y": 35.56, "diameter": 3.2},
        ],
        "corner_radius": 0,
    },
    "raspberry_pi": {
        "name": "Raspberry Pi HAT",
        "width": 65.0, "height": 56.5,
        "mounting_holes": [
            {"x": 3.5, "y": 3.5, "diameter": 2.75},
            {"x": 61.5, "y": 3.5, "diameter": 2.75},
            {"x": 3.5, "y": 52.5, "diameter": 2.75},
            {"x": 61.5, "y": 52.5, "diameter": 2.75},
        ],
        "corner_radius": 3.0,
    },
    "credit_card": {
        "name": "Credit Card Size",
        "width": 85.6, "height": 54.0,
        "mounting_holes": [
            {"x": 3.5, "y": 3.5, "diameter": 3.2},
            {"x": 82.1, "y": 3.5, "diameter": 3.2},
            {"x": 3.5, "y": 50.5, "diameter": 3.2},
            {"x": 82.1, "y": 50.5, "diameter": 3.2},
        ],
        "corner_radius": 3.0,
    },
    "custom": {
        "name": "Custom Size",
        "notes": "User-defined dimensions.",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH / LOOKUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def search_components(query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for components by name, category, or keywords."""
    query_lower = query.lower()
    results = []
    for key, comp in COMPONENTS.items():
        # Match against key, name, category, notes
        searchable = f"{key} {comp['name']} {comp['category']} {comp.get('notes', '')}".lower()
        if query_lower in searchable:
            if category and comp["category"].lower() != category.lower():
                continue
            results.append({"id": key, **comp})
    return results


def get_component(component_id: str) -> Optional[Dict[str, Any]]:
    """Get a single component by its ID."""
    comp = COMPONENTS.get(component_id)
    if comp:
        return {"id": component_id, **comp}
    return None


def get_components_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all components in a category."""
    return [
        {"id": key, **comp}
        for key, comp in COMPONENTS.items()
        if comp["category"].lower() == category.lower()
    ]


def list_categories() -> List[str]:
    """List all unique component categories."""
    return sorted(set(comp["category"] for comp in COMPONENTS.values()))


def get_edge_mount_components() -> List[Dict[str, Any]]:
    """Get components that mount to PCB edge (need enclosure cutouts)."""
    return [
        {"id": key, **comp}
        for key, comp in COMPONENTS.items()
        if comp.get("edge_mount", False)
    ]


def format_component_reference(components: List[str]) -> str:
    """Format component specs for AI prompt injection."""
    lines = []
    for comp_id in components:
        comp = COMPONENTS.get(comp_id)
        if not comp:
            continue
        body = comp["body"]
        lines.append(
            f"  • {comp['name']}: {body['x']}×{body['y']}×{body['z']}mm, "
            f"{comp['pins']}pins, {comp['mounting']}, pitch={comp.get('pitch', '?')}mm"
        )
        if comp.get("mating_face"):
            mf = comp["mating_face"]
            if "diameter" in mf:
                lines.append(f"    ↳ Enclosure cutout: ⌀{mf['diameter']}mm hole")
            else:
                lines.append(f"    ↳ Enclosure cutout: {mf['x']}×{mf['y']}mm opening")
        if comp.get("display_area"):
            da = comp["display_area"]
            lines.append(f"    ↳ Display window: {da['x']}×{da['y']}mm opening")
    return "\n".join(lines)
