import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

def create_sample_manual(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    warning_style = ParagraphStyle(
        'Warning_Custom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#C53030"),
        spaceAfter=8
    )

    story = []

    # --- PAGE 1: Overview and Specifications ---
    story.append(Paragraph("Dell Inspiron 15 5000 Series - Hardware Maintenance Manual", title_style))
    story.append(Paragraph("Document Part Number: MAN-5500-REV3", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Section 1: General Product Specifications & Architecture", h1_style))
    story.append(Paragraph(
        "This manual provides technical service information, diagnostic steps, and disassembly instructions "
        "for certified hardware technicians servicing the Dell Inspiron 15 5000 series notebooks. "
        "The computer features an Intel Core 11th Gen processor, dual-channel DDR4 SODIMM memory slots (supporting up to 32GB), "
        "M.2 PCIe NVMe solid-state storage, and an integrated thermal dissipation module with a variable-speed brushless DC fan.",
        body_style
    ))
    story.append(Paragraph(
        "Operating Temperature: 0°C to 35°C (32°F to 95°F). Storage Temperature: -40°C to 65°C (-40°F to 149°F). "
        "Relative Humidity: 10% to 90% (non-condensing).",
        body_style
    ))
    story.append(Paragraph(
        "Component layout includes the system board, heat-pipe assembly, exhaust fin stack, cooling fan unit, "
        "3-cell 42Wh or 4-cell 54Wh lithium-ion smart battery, and display hinge assembly.",
        body_style
    ))
    story.append(PageBreak())

    # --- PAGE 2: Safety Warnings and Electrostatic Precautions ---
    story.append(Paragraph("Section 2: Critical Safety Warnings and Electrostatic Precautions", h1_style))
    story.append(Paragraph(
        "SAFETY WARNING: High electrical current and mechanical hazards exist within the notebook chassis.",
        warning_style
    ))
    story.append(Paragraph(
        "1. Prior to removing any chassis covers or internal modules, always power down the computer completely, "
        "disconnect the AC power adapter from the wall outlet, and disconnect the internal battery cable from the system board. "
        "Failure to disconnect all power sources before servicing may result in electrical shock or catastrophic damage to motherboard microcircuits.",
        body_style
    ))
    story.append(Paragraph(
        "2. Thermal Hazard: The CPU and GPU heat sinks, heat pipes, and cooling fan exhaust vents can reach temperatures exceeding 70°C (158°F). "
        "Allow the system to cool for at least 15 minutes following operation before touching internal components.",
        body_style
    ))
    story.append(Paragraph(
        "3. Fan Spinning Hazard: Never use canned compressed air directly against cooling fan blades without immobilizing them. "
        "Uncontrolled spinning induced by high-pressure air can over-spin the bearings and generate back-EMF voltage that damages fan motor circuitry.",
        body_style
    ))
    story.append(Paragraph(
        "4. Electrostatic Discharge (ESD): Wear an ESD wrist grounding strap connected to an unpainted earth-grounded surface before touching memory modules, "
        "motherboard connectors, or PCIe cards.",
        body_style
    ))
    story.append(PageBreak())

    # --- PAGE 3: Thermal Management & Loud Fan Noise Troubleshooting ---
    story.append(Paragraph("Section 3: Cooling Fan and Thermal Noise Troubleshooting", h1_style))
    story.append(Paragraph(
        "Symptom: Laptop cooling fan is running continuously at excessive noise levels, spinning at maximum RPM, or producing unusual vibrating sounds.",
        body_style
    ))
    story.append(Paragraph("Likely Causes:", h1_style))
    story.append(Paragraph(
        "1. Dust, hair, and lint accumulation clogging the copper heatsink fins and trapping hot air inside the chassis.\n"
        "2. Obstructed ventilation grilles on the bottom and rear panels caused by using the laptop on soft surfaces (bedding, carpet, cushions).\n"
        "3. Dried or deteriorated thermal interface material (thermal paste) between the CPU/GPU die and the copper heat spreader.\n"
        "4. Outdated BIOS firmware with aggressive or uncalibrated thermal fan control curves.\n"
        "5. Fan mechanical wear: Ball bearing or fluid dynamic bearing failure causing grinding, rattling, or whining noises.",
        body_style
    ))
    story.append(Paragraph("Step-by-Step Diagnostic & Repair Procedures (Easiest First):", h1_style))
    story.append(Paragraph(
        "Step 1 - Improve Airflow (Non-Invasive):\n"
        "Ensure the notebook is placed on a hard, flat, level surface (such as a desk). Avoid lap, bed, or cloth usage that seals intake vents. "
        "Ensure at least 10 cm (4 inches) of clearance around all exhaust vents.",
        body_style
    ))
    story.append(Paragraph(
        "Step 2 - External Vent Cleaning:\n"
        "Shut down the laptop and disconnect power. Using a can of compressed air held strictly upright, deliver short, gentle 1-2 second bursts "
        "into the intake vents on the bottom cover and exhaust vents at the rear hinge. Keep the nozzle at least 5 cm away.",
        body_style
    ))
    story.append(Paragraph(
        "Step 3 - BIOS and Power Management Thermal Profiles:\n"
        "Reboot the laptop and press F2 to enter BIOS Setup. Verify Thermal Management settings. Ensure BIOS is updated to version 1.14.0 or newer. "
        "In Windows, open Dell Power Manager and select the 'Quiet' or 'Cool' thermal profile to limit acoustic fan curves.",
        body_style
    ))
    story.append(Paragraph(
        "Step 4 - Internal Heatsink Fin Inspection:\n"
        "SAFETY WARNING: Disconnect AC adapter and disconnect battery first. Unscrew the 8 Phillips screws securing the bottom base cover. "
        "Gently pry off the base cover using a plastic scribe. Inspect the fan shroud and copper fin stack. "
        "Remove accumulated 'dust mat' lint between the fan outlet and radiator fins using tweezers and ESD-safe brush.",
        body_style
    ))
    story.append(Paragraph(
        "Step 5 - Thermal Paste Re-application and Fan Replacement:\n"
        "If the fan produces a mechanical grinding or buzzing sound (bearing wear), replace the fan assembly (Dell Part #01HW420). "
        "If temperatures remain above 85°C at idle, unfasten the heatsink screws in reverse diagonal order (4, 3, 2, 1), "
        "clean old thermal compound with 99% isopropyl alcohol, and apply a pea-sized dot of high-grade non-conductive thermal paste.",
        body_style
    ))
    story.append(Paragraph(
        "Missing Information Check: If the user has not specified whether the fan sound is a loud rush of high-speed air or a rattling/grinding mechanical sound, "
        "technicians should ask: 'Is the loud fan noise a fast rushing air sound from high speeds, or a mechanical rattling/buzzing/grinding sound?'",
        body_style
    ))
    story.append(PageBreak())

    # --- PAGE 4: Battery, Power, and RAM Maintenance ---
    story.append(Paragraph("Section 4: Battery Health and Memory (RAM) Maintenance", h1_style))
    story.append(Paragraph(
        "Battery Diagnostic Steps:\n"
        "If notebook fails to boot or battery discharges abnormally fast, press F12 during power-on to run Dell ePSA Pre-boot Diagnostics. "
        "Check battery health status. A battery showing 'End of Usable Life' or swelling requires immediate replacement. "
        "WARNING: Swollen lithium-ion batteries must never be punctured or compressed.",
        body_style
    ))
    story.append(Paragraph(
        "Memory Installation Procedure:\n"
        "1. Disconnect battery and press power button for 5 seconds to drain flea power.\n"
        "2. Spread retaining clips on the SODIMM socket outward until memory module pops up at 30-degree angle.\n"
        "3. Pull memory module out of socket.\n"
        "4. Align notch on replacement DDR4 SODIMM with socket key and press down until clips engage.",
        body_style
    ))

    doc.build(story)
    print(f"Sample manual generated successfully at: {output_path}")

if __name__ == "__main__":
    out_dir = r"C:\Users\prera\.gemini\antigravity\scratch\ai_tech_support\manuals"
    os.makedirs(out_dir, exist_ok=True)
    pdf_file = os.path.join(out_dir, "Dell_Inspiron_Hardware_Maintenance_Manual.pdf")
    create_sample_manual(pdf_file)

