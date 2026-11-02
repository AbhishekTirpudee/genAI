"""
Generates a valid, multi-page PDF electronic component catalogue
using standard Python without requiring reportlab or external PDF libraries.
"""

def generate_pdf():
    # Simple valid PDF 1.4 generator
    pages_content = [
        # Page 1: Title and Microcontrollers
        """
BT
/F1 18 Tf
50 750 Td
(ELECTRONIC COMPONENTS CATALOGUE - 2026 EDITION) Tj
0 -25 Td
/F1 12 Tf
(ElectroRAG Reference Datasheet & Pricing Guide) Tj
0 -35 Td
/F1 14 Tf
(1. Microcontrollers & Wireless) Tj
0 -20 Td
/F1 10 Tf
(Part: ESP32-WROOM-32 | Category: Wireless MCU | Operating Voltage: 3.3V) Tj
0 -15 Td
(Specs: 240MHz Xtensa LX6 Dual-Core, 520KB SRAM, 4MB Flash, Wi-Fi 802.11b/g/n, BLE 4.2) Tj
0 -15 Td
(Applications: IoT Home Automation, Smart Plugs, Wearables, Wireless Sensor Nodes) Tj
0 -15 Td
(Pricing: 1 pc: $3.85 | 10 pcs: $3.45 | 100 pcs: $2.95 | 1000 pcs: $2.45) Tj
0 -25 Td
(Part: STM32F401RET6 | Category: 32-bit ARM MCU | Operating Voltage: 1.7V - 3.6V) Tj
0 -15 Td
(Specs: 84MHz Cortex-M4 FPU, 512KB Flash, 96KB SRAM, 50 GPIOs, LQFP-64) Tj
0 -15 Td
(Applications: Medical Instrumentation, Industrial PLC, Flight Controllers) Tj
0 -15 Td
(Pricing: 1 pc: $5.20 | 10 pcs: $4.65 | 100 pcs: $3.90 | 1000 pcs: $3.15) Tj
0 -25 Td
(Part: ATmega328P-PU | Category: 8-bit AVR MCU | Operating Voltage: 1.8V - 5.5V) Tj
0 -15 Td
(Specs: 20MHz, 32KB Flash, 2KB SRAM, 1KB EEPROM, 23 GPIOs, PDIP-28) Tj
0 -15 Td
(Applications: Arduino Uno Projects, DIY Hobbyist, Robotics, Simple Controllers) Tj
0 -15 Td
(Pricing: 1 pc: $2.15 | 10 pcs: $1.95 | 100 pcs: $1.65 | 1000 pcs: $1.35) Tj
ET
""",
        # Page 2: Power Regulators & Op-Amps
        """
BT
/F1 16 Tf
50 750 Td
(2. Power Regulators & Analog ICs) Tj
0 -30 Td
/F1 10 Tf
(Part: AMS1117-3.3 | Category: LDO Linear Regulator | Input Voltage: 4.75V - 12V) Tj
0 -15 Td
(Specs: Output: 3.3V Fixed, 1.0A Max Current, 1.1V Dropout, Package: SOT-223) Tj
0 -15 Td
(Applications: 5V to 3.3V Step-down for ESP32/STM32, Battery Chargers) Tj
0 -15 Td
(Pricing: 1 pc: $0.32 | 10 pcs: $0.25 | 100 pcs: $0.18 | 1000 pcs: $0.11) Tj
0 -25 Td
(Part: LM7805CT | Category: Linear Voltage Regulator | Input Voltage: 7V - 25V) Tj
0 -15 Td
(Specs: Output: 5.0V Fixed, 1.5A Max Current, Thermal Protection, Package: TO-220) Tj
0 -15 Td
(Applications: 5V TTL Logic Supplies, Arduino DC Power, Local Regulation) Tj
0 -15 Td
(Pricing: 1 pc: $0.65 | 10 pcs: $0.55 | 100 pcs: $0.42 | 1000 pcs: $0.32) Tj
0 -25 Td
(Part: LM358N | Category: Dual Operational Amplifier | Supply: 3V - 32V) Tj
0 -15 Td
(Specs: 1.0MHz Bandwidth, 500uA Current, 2mV Offset, 2 Channels, DIP-8) Tj
0 -15 Td
(Applications: Transducer Amps, Active Filters, DC Gain Blocks, Comparators) Tj
0 -15 Td
(Pricing: 1 pc: $0.45 | 10 pcs: $0.38 | 100 pcs: $0.28 | 1000 pcs: $0.18) Tj
0 -25 Td
(Part: NE555P | Category: Precision Timer | Supply: 4.5V - 16V) Tj
0 -15 Td
(Specs: Astable/Monostable Modes, Up to 500kHz, 200mA Drive, DIP-8) Tj
0 -15 Td
(Applications: Pulse Generators, Delay Timers, PWM Motor Speed Control) Tj
0 -15 Td
(Pricing: 1 pc: $0.35 | 10 pcs: $0.29 | 100 pcs: $0.22 | 1000 pcs: $0.14) Tj
ET
""",
        # Page 3: Sensors & Discretes
        """
BT
/F1 16 Tf
50 750 Td
(3. Sensors & Discrete Semiconductors) Tj
0 -30 Td
/F1 10 Tf
(Part: DHT22 / AM2302 | Category: Digital Humidity & Temp Sensor | Supply: 3.3V - 6V) Tj
0 -15 Td
(Specs: 0-100% RH [+/-2%], -40 to +80 C [+/-0.5 C], 1-wire digital output) Tj
0 -15 Td
(Applications: HVAC Systems, Greenhouse Control, Weather Monitoring) Tj
0 -15 Td
(Pricing: 1 pc: $4.50 | 10 pcs: $3.95 | 100 pcs: $3.20 | 1000 pcs: $2.50) Tj
0 -25 Td
(Part: MPU-6050 | Category: 6-Axis Motion Tracking | Supply: 2.37V - 3.46V) Tj
0 -15 Td
(Specs: 3-Axis Gyro +/-2000 dps, 3-Axis Accel +/-16g, I2C, Onboard DMP, QFN-24) Tj
0 -15 Td
(Applications: Drones, Robotic Self-Balancing, Attitude Estimation) Tj
0 -15 Td
(Pricing: 1 pc: $2.80 | 10 pcs: $2.40 | 100 pcs: $1.95 | 1000 pcs: $1.50) Tj
0 -25 Td
(Part: IRFZ44N | Category: N-Channel Power MOSFET | Max Voltage: 55V) Tj
0 -15 Td
(Specs: Continuous Id: 49A, Rds(on): 17.5 mOhm, 94W, Package: TO-220AB) Tj
0 -15 Td
(Applications: Motor H-Bridges, Speed Controllers, SMPS, Battery Disconnects) Tj
0 -15 Td
(Pricing: 1 pc: $1.10 | 10 pcs: $0.95 | 100 pcs: $0.75 | 1000 pcs: $0.58) Tj
ET
"""
    ]

    objects = []
    
    def add_object(content):
        objects.append(content)
        return len(objects)

    # 1: Font
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Content streams & Page objects
    page_ids = []
    for stream_text in pages_content:
        stream_bytes = stream_text.strip().encode('latin1')
        stream_len = len(stream_bytes)
        content_id = add_object(f"<< /Length {stream_len} >>\nstream\n{stream_text.strip()}\nendstream")
        page_id = add_object(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>")
        page_ids.append(page_id)

    # 2: Pages tree
    pages_str = " ".join([f"{p} 0 R" for p in page_ids])
    pages_obj = f"<< /Type /Pages /Kids [{pages_str}] /Count {len(page_ids)} >>"
    
    # We reserved index 1 for font, so let's put Pages tree as index 2
    objects.insert(1, pages_obj)

    # Catalog
    catalog_id = len(objects) + 1
    objects.append(f"<< /Type /Catalog /Pages 2 0 R >>")

    # Build file
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode('latin1'))

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode('latin1'))
    for off in offsets:
        output.extend(f"{off:010d} 00000 n \n".encode('latin1'))

    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin1'))

    with open("electronic_components_catalogue.pdf", "wb") as f:
        f.write(output)

    print("[*] Generated electronic_components_catalogue.pdf successfully!")

if __name__ == "__main__":
    generate_pdf()
