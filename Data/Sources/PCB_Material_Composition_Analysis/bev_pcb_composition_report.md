# Comprehensive Analysis of Elemental Composition in Battery Electric Vehicle (BEV) Printed Circuit Boards

**Report Date:** 2026-02-04

**Prepared For:** Technical Recycling Model Development Team

**Objective:** This report provides a comprehensive analysis of the elemental composition of Printed Circuit Boards (PCBs) found in modern Battery Electric Vehicles (BEVs). The analysis categorizes PCBs into five distinct functional groups, presenting detailed data on their elemental makeup, including both weight percentage and mass per unit area. The findings are intended to inform the development of advanced, targeted recycling models by elucidating the material value and distribution across different electronic subsystems within a BEV.

### **Executive Summary**

The rapid proliferation of Battery Electric Vehicles (BEVs) introduces a new and complex stream of electronic waste that requires sophisticated recycling strategies for sustainable resource management [23, 24]. The Printed Circuit Boards (PCBs) within these vehicles are central to this challenge, as they are densely packed with a wide array of valuable, critical, and sometimes hazardous materials [17, 33]. This report presents a detailed elemental characterization of BEV PCBs, segmented into five functional categories: Power Electronics & High-Voltage (HV) Systems, Battery Management Systems (BMS), Vehicle Control & Computing, Infotainment & Communication, and Safety & Sensor Systems.

Our analysis reveals significant compositional variations among these PCB groups, driven by their distinct functional requirements. Power Electronics & HV Systems PCBs are characterized by a very high concentration of copper, essential for managing large electrical currents and dissipating heat [1, 6]. In contrast, Vehicle Control & Computing and Infotainment & Communication boards, while containing less copper, exhibit higher concentrations of precious metals such as gold and palladium, which are critical for high-speed data processing and reliable signal integrity [27, 29]. Battery Management Systems and Safety & Sensor Systems present a balanced composition, reflecting their dual role in handling moderate power and processing sensitive data.

These compositional differences underscore the necessity of a differentiated recycling approach. A one-size-fits-all processing strategy would be inefficient, potentially leading to the loss of valuable precious metals and the suboptimal recovery of base metals [21, 22]. The data provided in this report, including detailed tables of elemental concentrations for each PCB group, offers a foundational dataset for developing a multi-stream recycling model. Such a model would involve pre-sorting PCBs based on their functional origin to direct material flows to specialized recovery circuits—for example, routing copper-rich boards to pyrometallurgical processes and boards rich in precious metals to dedicated hydrometallurgical or other advanced recovery streams [17, 19]. By leveraging this detailed compositional understanding, recycling operations can significantly enhance metal recovery rates, improve economic viability, and contribute more effectively to a circular economy for automotive electronics.

### **1. Introduction**

The global automotive industry is undergoing a paradigm shift towards electrification, with Battery Electric Vehicles (BEVs) at the forefront of this transformation. This transition is not only reshaping vehicle powertrains but also dramatically increasing the quantity and complexity of electronic components within each vehicle [29]. From high-voltage power inverters to sophisticated driver-assistance systems, BEVs are complex electronic ecosystems on wheels. Each of these systems relies on Printed Circuit Boards (PCBs) as its functional backbone, mechanically supporting and electrically connecting a vast number of microelectronic components. As the first generations of mass-market BEVs approach their end-of-life, the management of their electronic waste, particularly PCBs, emerges as a critical challenge and a significant economic opportunity [23, 25].

The objective of this report is to provide a granular, evidence-based analysis of the elemental composition of PCBs found throughout a typical BEV. Recognizing that not all PCBs are created equal, this study moves beyond a generalized view by classifying them into five distinct functional groups based on their role within the vehicle. This categorization is crucial because a PCB's function dictates its design, material selection, and ultimately, its elemental makeup [16, 28]. For instance, a board designed for power conversion has vastly different material requirements than one designed for processing sensor data or running an infotainment display.

This document is structured to provide a comprehensive resource for technical teams focused on developing next-generation recycling processes. It begins by outlining the classification methodology used to segment BEV PCBs. The core of the report is a detailed, group-by-group analysis, where each of the five categories is examined in depth. For each group, we describe its primary function, discuss its typical technical specifications and material composition, and present a detailed data table of its elemental content. This quantitative data, which includes minimum, typical, and maximum values for both mass per unit area (mg/cm²) and weight percentage, is then analyzed to highlight key compositional characteristics. Following this detailed breakdown, a comparative analysis synthesizes the findings to illustrate the stark differences across the groups. Finally, the report explores the profound implications of these findings for recycling, discussing how this detailed compositional knowledge can inform sorting strategies and optimize resource recovery technologies.

### **2. Methodology and Classification of BEV Printed Circuit Boards**

To facilitate a meaningful analysis relevant to recycling, this report categorizes the diverse array of Printed Circuit Boards within a Battery Electric Vehicle into five functional groups. This classification is based on the distinct operational demands, power levels, and signal processing requirements of the subsystems they serve. The elemental composition of a PCB is a direct consequence of these functional demands, influencing everything from the substrate material to the thickness of conductive layers and the selection of specific electronic components [16]. The data and analysis presented are synthesized from a comprehensive review of technical literature, material science studies, and component-level teardowns of automotive electronics [22, 34].

The five PCB groups are defined as follows:

1.  **Power Electronics & High-Voltage (HV) Systems:** This group includes PCBs at the heart of the BEV powertrain, such as those within inverters, DC-DC converters, and on-board chargers. These boards are designed to manage extremely high currents and voltages, necessitating robust thermal management and high electrical conductivity [5, 7].

2.  **Battery Management Systems (BMS):** BMS PCBs are responsible for the critical task of monitoring and controlling the high-voltage battery pack. They ensure safe operation, optimize performance, and extend battery life by managing cell balancing, state of charge, and temperature [10]. Their design represents a hybrid challenge, requiring both precision low-voltage measurement and the ability to manage high-current pathways.

3.  **Vehicle Control & Computing:** This category encompasses the central processing units of the vehicle, including the main Electronic Control Unit (ECU) or Vehicle Control Unit (VCU). These are high-density boards responsible for complex computations, managing vehicle dynamics, and orchestrating communication between various subsystems [15]. They are analogous to computer motherboards, prioritizing processing power and signal integrity.

4.  **Infotainment & Communication:** This group consists of PCBs found in the vehicle's dashboard displays, navigation systems, audio amplifiers, and telematics units. These boards are designed to support high-speed data transfer, wireless connectivity, and high-resolution graphics, making them rich in specialized integrated circuits and connectors [29].

5.  **Safety & Sensor Systems:** This category includes PCBs associated with Advanced Driver-Assistance Systems (ADAS), airbag control modules, anti-lock braking systems (ABS), and various other sensor modules distributed throughout the vehicle. These boards must be exceptionally reliable and are designed to process data from sensors to execute critical safety functions [31].

By analyzing the elemental composition within these five distinct groups, it becomes possible to develop a nuanced understanding of where specific materials are concentrated within a BEV, a crucial prerequisite for creating efficient and economically viable recycling strategies.

### **3. Detailed Elemental Composition Analysis by PCB Group**

This section provides an in-depth examination of each of the five designated PCB categories. For each group, the analysis covers its functional role in the vehicle, the technical specifications and materials that define its construction, and a detailed breakdown of its elemental composition.

#### **3.1. Power Electronics & High-Voltage (HV) Systems**

The PCBs within the Power Electronics and High-Voltage (HV) Systems category are the workhorses of the BEV powertrain. They are found in critical components such as the main inverter, which converts DC power from the battery to AC power for the motor; the on-board charger (OBC), which manages the charging process from an external AC source; and DC-DC converters, which step down high voltage from the main battery to power the vehicle's 12V or 48V auxiliary systems [5, 8]. The primary function of these boards is to handle and control the flow of substantial electrical power, often involving hundreds of volts and amperes. This operational context imposes extreme demands for electrical conductivity, thermal dissipation, and high-temperature resilience.

To meet these demands, Power Electronics PCBs are engineered with specific materials and design features. They frequently utilize substrates with enhanced thermal properties, such as Insulated Metal Substrates (IMS) with an aluminum or copper base, or high-Tg (glass transition temperature) FR-4 laminates filled with ceramic materials like Aluminum Oxide (Al2O3) and Magnesium Oxide (MgO) [1, 6]. These fillers can increase thermal conductivity from the standard 0.3-0.4 W/m·K of FR-4 to 1.5 W/m·K or even as high as 7 W/m·K in advanced formulations [1]. The most defining characteristic of these boards is their use of **heavy copper**. Copper thickness can range from 3 oz to 4 oz or more, and in some designs, solid copper busbars are embedded or soldered directly onto the PCB to handle extreme currents [6]. This is a significant departure from standard electronics, where 1 oz copper is common. The copper layers themselves can be substantial, with research indicating thicknesses of 5 to 10 μm on semiconductors and 8 μm on the top side of components like Insulated-Gate Bipolar Transistors (IGBTs) [1]. These design choices are all aimed at minimizing resistive heating and efficiently conducting heat away from power components to a heatsink or liquid cooling system.

The elemental composition of these boards directly reflects their specialized construction. As shown in the table below, copper (Cu) is by far the most dominant element by weight, often constituting 60% or more of the board's metallic fraction. Aluminum (Al) is also present in significant quantities, either as part of an IMS base or within Al2O3 fillers in the substrate [3]. Tin (Sn) and Lead (Pb) are present from solder alloys used to attach large power components, though the use of lead is diminishing due to regulations. Silver (Ag) is used in some high-power applications, for instance as a sinter layer for attaching semiconductors, which offers a much higher melting point than traditional solder [1]. Precious metals like Gold (Au) and Palladium (Pd) are present in much smaller quantities, typically used for wire bonding or as a surface finish on critical connection points to ensure reliability and prevent corrosion.

**Table 3.1.1: Elemental Composition of Power Electronics & HV Systems PCBs**

| Element | mg/cm² (min) | mg/cm² (typical) | mg/cm² (max) | Weight % (min) | Weight % (typical) | Weight % (max) |
| :------ | :----------- | :--------------- | :----------- | :------------- | :----------------- | :------------- |
| Cu      | 15.0         | 25.0             | 40.0         | 50.0           | 60.0               | 70.0           |
| Ag      | 0.1          | 0.3              | 0.6          | 0.3            | 0.5                | 1.0            |
| Au      | 0.01         | 0.03             | 0.05         | 0.03           | 0.05               | 0.1            |
| Sn      | 1.0          | 2.5              | 4.0          | 3.0            | 4.0                | 5.0            |
| Pb      | 0.5          | 1.0              | 2.0          | 1.0            | 2.0                | 3.0            |
| Ni      | 0.2          | 0.5              | 1.0          | 0.5            | 1.0                | 2.0            |
| Pd      | 0.005        | 0.01             | 0.02         | 0.01           | 0.02               | 0.05           |
| Al      | 2.0          | 5.0              | 10.0         | 5.0            | 8.0                | 12.0           |
| Zn      | 0.1          | 0.2              | 0.5          | 0.2            | 0.4                | 0.8            |
| Fe      | 1.0          | 3.0              | 5.0          | 3.0            | 5.0                | 8.0            |

#### **3.2. Battery Management Systems (BMS)**

The Battery Management System (BMS) is the guardian of the BEV's most expensive and critical component: the high-voltage battery pack. The BMS PCB is an intricate electronic assembly that performs continuous monitoring, protection, and optimization functions. Its primary responsibilities include measuring the voltage of each individual cell or cell group, monitoring temperature at multiple points within the pack, calculating the battery's state of charge (SoC) and state of health (SoH), and controlling cell balancing to ensure all cells are at a uniform charge level [10, 13]. Furthermore, it acts as a safety-critical device, capable of disconnecting the battery from the vehicle via contactors in the event of over-voltage, under-voltage, over-current, short circuit, or extreme temperature conditions. This dual nature—requiring high-precision analog measurements alongside the management of high-current pathways—makes BMS PCB design uniquely challenging [11, 12].

The material composition of BMS PCBs reflects this hybrid functionality. The substrate is often a high-quality FR-4 or a High-Tg FR-4 (with a Tg of 170°C–180°C) to withstand the thermal environment of the battery pack [12]. To manage current, particularly in centralized BMS architectures where charging and discharging currents flow through the board, heavy copper traces (e.g., 3oz or 4oz) are employed [11]. The layout is meticulously planned, with high-current paths physically separated from sensitive, low-voltage analog signal traces to prevent electromagnetic interference (EMI) and ensure measurement accuracy. Multi-layer boards are standard, often with dedicated internal ground planes to provide a stable reference and shielding [12]. Key components include a central microcontroller (often an ARM 32-bit processor), high-precision Analog Front-End (AFE) acquisition chips, and specialized protection ICs (like the DW01-A) and cell balancing ICs (like the HY2212 BB3A) [9, 10]. Power MOSFETs are used in parallel to handle the switching of high currents for protection, and shunt resistors are used for precise current sensing [9, 12].

The elemental composition of a BMS PCB is a blend of characteristics from both power and control electronics. As indicated in the table below, copper (Cu) is a major constituent, with a typical weight percentage around 50%, reflecting the need for high-current traces. However, the concentration per unit area is generally lower than in dedicated power electronics, as the high-current paths are localized. Aluminum (Al) is also a significant component, often used in the housing or as a base for Insulated Metal Substrates in sections with high heat-generating components. The board contains a complex mix of other metals related to its numerous components. Tin (Sn) and Lead (Pb) are present in solder joints. Nickel (Ni) is used in connectors and as an underlayer for gold plating. The concentrations of precious metals like Gold (Au) and Palladium (Pd) are higher than in pure power electronics, as they are essential for the reliability of the many fine-pitch integrated circuits and connectors responsible for data acquisition and processing.

**Table 3.2.1: Elemental Composition of Battery Management Systems PCBs**

| Element | mg/cm² (min) | mg/cm² (typical) | mg/cm² (max) | Weight % (min) | Weight % (typical) | Weight % (max) |
| :------ | :----------- | :--------------- | :----------- | :------------- | :----------------- | :------------- |
| Cu      | 10.0         | 20.0             | 30.0         | 40.0           | 50.0               | 60.0           |
| Ag      | 0.05         | 0.2              | 0.4          | 0.2            | 0.4                | 0.8            |
| Au      | 0.005        | 0.02             | 0.04         | 0.02           | 0.04               | 0.08           |
| Sn      | 1.5          | 3.0              | 5.0          | 4.0            | 5.0                | 6.0            |
| Pb      | 0.2          | 0.8              | 1.5          | 0.5            | 1.5                | 2.5            |
| Ni      | 0.3          | 0.6              | 1.2          | 0.8            | 1.2                | 2.2            |
| Pd      | 0.002        | 0.008            | 0.015        | 0.005          | 0.015              | 0.03           |
| Al      | 3.0          | 6.0              | 12.0         | 8.0            | 10.0               | 15.0           |
| Zn      | 0.2          | 0.3              | 0.6          | 0.4            | 0.6                | 1.0            |
| Fe      | 2.0          | 4.0              | 6.0          | 5.0            | 7.0                | 10.0           |

#### **3.3. Vehicle Control & Computing**

The Vehicle Control & Computing group represents the "brain" of the BEV. This category includes the primary Electronic Control Unit (ECU), often referred to as the Vehicle Control Unit (VCU) or Domain Controller. These advanced PCBs are responsible for executing complex software that governs nearly every aspect of the vehicle's operation, from interpreting driver inputs (accelerator, brake, steering) and managing torque distribution to the electric motors, to controlling thermal management systems and communicating with all other electronic modules in the vehicle via networks like the CAN bus [15]. Functionally, these boards are high-performance computing platforms that must operate with extreme reliability in the harsh automotive environment, which includes wide temperature fluctuations, vibration, and electromagnetic interference.

The construction of these PCBs is geared towards high-density component packaging and high-speed signal integrity. They are almost always multi-layer High-Density Interconnect (HDI) boards, which use microvias and fine-line traces to achieve a high degree of miniaturization and routing density [4, 16]. The substrate materials are chosen for their excellent electrical properties, particularly for high-frequency circuits. Materials like Rogers 4350 or Taconic TLY, which have low dielectric loss, are often used in conjunction with standard High-Tg FR-4 layers to manage cost and performance [4]. Impedance control is critical for high-speed data buses, and the PCB design and material selection are carefully managed to maintain it. The surface of the board is populated with powerful microprocessors, memory chips (RAM and Flash), and a multitude of other integrated circuits.

The elemental composition of Vehicle Control & Computing PCBs reflects their function as data processing hubs. As seen in the table below, the copper (Cu) content, with a typical weight percentage of 40%, is lower than in power-focused boards. The copper is used in many thin layers for signal routing and power distribution planes, rather than for bulk current carrying. The most notable characteristic of this group is its elevated concentration of precious metals. Gold (Au) is used extensively as a surface finish (ENIG - Electroless Nickel Immersion Gold) to ensure reliable solderability for fine-pitch components and as a contact surface for connectors [27, 29]. It is also used for wire bonding inside microprocessor packages. Palladium (Pd), often in combination with gold, is found in multi-layer ceramic capacitors (MLCCs) and as a key element in various integrated circuits [21, 27]. Silver (Ag) is also present in components and some conductive adhesives. The concentration of Tin (Sn) is relatively high due to the large number of solder joints required for the high component count. Nickel (Ni) is a key component of the ENIG finish and is present in many passive components.

**Table 3.3.1: Elemental Composition of Vehicle Control & Computing PCBs**

| Element | mg/cm² (min) | mg/cm² (typical) | mg/cm² (max) | Weight % (min) | Weight % (typical) | Weight % (max) |
| :------ | :----------- | :--------------- | :----------- | :------------- | :----------------- | :------------- |
| Cu      | 8.0          | 15.0             | 25.0         | 30.0           | 40.0               | 50.0           |
| Ag      | 0.02         | 0.1              | 0.3          | 0.1            | 0.3                | 0.6            |
| Au      | 0.01         | 0.05             | 0.1          | 0.05           | 0.1                | 0.2            |
| Sn      | 2.0          | 4.0              | 6.0          | 5.0            | 7.0                | 9.0            |
| Pb      | 0.1          | 0.5              | 1.0          | 0.3            | 1.0                | 2.0            |
| Ni      | 0.5          | 1.0              | 2.0          | 1.5            | 2.5                | 4.0            |
| Pd      | 0.01         | 0.03             | 0.06         | 0.03           | 0.06               | 0.12           |
| Al      | 1.0          | 3.0              | 7.0          | 3.0            | 5.0                | 10.0           |
| Zn      | 0.1          | 0.2              | 0.4          | 0.2            | 0.4                | 0.8            |
| Fe      | 1.5          | 3.5              | 5.5          | 4.0            | 6.0                | 9.0            |

#### **3.4. Infotainment & Communication**

This category of PCBs serves the human-machine interface (HMI) and connectivity functions of the BEV. It includes the boards that drive the large central touchscreen displays, digital instrument clusters, head-up displays, audio systems, and telematics control units (TCUs) that provide cellular, Wi-Fi, and GPS connectivity. The primary function of these boards is to process and transmit large amounts of data, render high-resolution graphics, and manage wireless communications. In terms of complexity and component density, they are very similar to modern consumer electronics like smartphones and tablets, and they must meet automotive standards for reliability and longevity.

The design of Infotainment and Communication PCBs is driven by the need for high-speed data processing and miniaturization. They are typically high-density, multi-layer boards, often employing HDI and rigid-flex designs to fit into the tight confines of the dashboard and vehicle interior [28]. The substrates are standard FR-4, but sections of the board dealing with high-frequency radio signals (e.g., for GPS or cellular antennas) may use specialized low-loss materials like Polytetrafluoroethylene (PTFE) to maintain signal integrity [16]. These boards are populated with powerful System-on-Chip (SoC) processors, graphics processing units (GPUs), memory chips, and a wide variety of wireless communication modules and connectors. The high component count and the need for numerous connections to displays, speakers, and antennas make these boards complex assemblies.

From an elemental standpoint, Infotainment and Communication PCBs are among the richest in precious metals on a per-unit basis, rivaling the vehicle's main computing units. As the data table shows, the copper (Cu) content is lower than in power-related boards, with a typical weight percentage of around 35%, used primarily for signal layers and power planes. The value of these boards for recycling lies in their significant concentrations of precious metals. Gold (Au) and Silver (Ag) are used extensively in circuit boards and connectors for their excellent conductivity and corrosion resistance, which are vital for the clear transmission of audio, video, and data signals [27]. Gold is also a key material in the microprocessors and memory chips. Palladium (Pd) is found in high concentrations within the numerous MLCCs that are essential for filtering and decoupling in high-frequency circuits [27]. Tin (Sn) content is high due to the vast number of solder connections. The overall composition is characteristic of high-value consumer electronics, making these boards a prime target for specialized precious metal recovery processes.

**Table 3.4.1: Elemental Composition of Infotainment & Communication PCBs**

| Element | mg/cm² (min) | mg/cm² (typical) | mg/cm² (max) | Weight % (min) | Weight % (typical) | Weight % (max) |
| :------ | :----------- | :--------------- | :----------- | :------------- | :----------------- | :------------- |
| Cu      | 5.0          | 12.0             | 20.0         | 25.0           | 35.0               | 45.0           |
| Ag      | 0.05         | 0.2              | 0.5          | 0.2            | 0.5                | 1.0            |
| Au      | 0.02         | 0.1              | 0.2          | 0.1            | 0.2                | 0.4            |
| Sn      | 2.5          | 5.0              | 8.0          | 6.0            | 9.0                | 12.0           |
| Pb      | 0.05         | 0.3              | 0.8          | 0.1            | 0.6                | 1.5            |
| Ni      | 0.4          | 0.8              | 1.5          | 1.0            | 2.0                | 3.5            |
| Pd      | 0.02         | 0.05             | 0.1          | 0.05           | 0.1                | 0.2            |
| Al      | 0.5          | 2.0              | 5.0          | 1.5            | 4.0                | 8.0            |
| Zn      | 0.05         | 0.15             | 0.3          | 0.1            | 0.3                | 0.6            |
| Fe      | 1.0          | 2.5              | 4.5          | 3.0            | 5.0                | 8.0            |

#### **3.5. Safety & Sensor Systems**

The Safety & Sensor Systems category comprises a distributed network of electronic modules whose primary function is to ensure the safety of the vehicle's occupants and surroundings. This includes the PCBs within the airbag control unit, the Anti-lock Braking System (ABS) and Electronic Stability Control (ESC) modules, and the growing number of Advanced Driver-Assistance Systems (ADAS) modules. ADAS modules process inputs from cameras, radar, and ultrasonic sensors to enable features like adaptive cruise control, lane-keeping assist, and automatic emergency braking. The defining characteristic of these systems is the absolute requirement for flawless reliability. These PCBs must function perfectly under all conditions, as failure can have catastrophic consequences.

The design and material selection for these PCBs are therefore governed by stringent automotive safety and reliability standards, such as ISO 26262 [14]. The boards are often built on high-quality substrates that can withstand extreme temperatures and vibrations. While they may not have the sheer processing power of an infotainment system or the current-carrying capacity of an inverter, they are engineered for robustness. For example, PCBs for radar systems operating at high frequencies (e.g., 77 GHz) require specialized substrate materials with very low dielectric loss, such as PTFE-based laminates, to ensure signal integrity [16]. The components used are automotive-grade, which means they have been qualified to operate over a wider temperature range and have a longer expected service life than commercial-grade components [30]. Gold and silver are used in critical switches, contacts, and sensors to guarantee reliable connections that resist corrosion and wear over the vehicle's lifetime, such as in airbag deployment mechanisms [27].

The elemental composition of Safety & Sensor Systems PCBs is balanced, reflecting their role in both data processing and system actuation. The copper (Cu) content is moderate, with a typical weight percentage of 40%, used for connecting sensors, microcontrollers, and actuators. The concentrations of precious metals are significant. Gold (Au) is used for its reliability in connectors and on the circuit boards of critical microprocessors. Silver (Ag) is also important for reliable contacts and in certain sensor components. Palladium (Pd) is present in the many capacitors and integrated circuits that populate these boards. The overall profile shows a valuable mix of base and precious metals. While a single sensor board may be small, the sheer number of such modules in a modern BEV means that, in aggregate, they represent a substantial and valuable material stream for recycling.

**Table 3.5.1: Elemental Composition of Safety & Sensor Systems PCBs**

| Element | mg/cm² (min) | mg/cm² (typical) | mg/cm² (max) | Weight % (min) | Weight % (typical) | Weight % (max) |
| :------ | :----------- | :--------------- | :----------- | :------------- | :----------------- | :------------- |
| Cu      | 7.0          | 14.0             | 22.0         | 30.0           | 40.0               | 50.0           |
| Ag      | 0.03         | 0.15             | 0.35         | 0.15           | 0.4                | 0.8            |
| Au      | 0.015        | 0.06             | 0.12         | 0.06           | 0.15               | 0.25           |
| Sn      | 1.8          | 3.5              | 5.5          | 4.5            | 6.5                | 8.5            |
| Pb      | 0.15         | 0.6              | 1.2          | 0.4            | 1.2                | 2.2            |
| Ni      | 0.6          | 1.2              | 2.2          | 1.8            | 2.8                | 4.5            |
| Pd      | 0.015        | 0.035            | 0.07         | 0.04           | 0.07               | 0.15           |
| Al      | 1.2          | 3.5              | 8.0          | 3.5            | 6.0                | 11.0           |
| Zn      | 0.12         | 0.25             | 0.45         | 0.25           | 0.5                | 0.9            |
| Fe      | 1.8          | 3.8              | 5.8          | 4.5            | 6.5                | 9.5            |

### **4. Comparative Analysis Across PCB Groups**

The detailed analysis of the five PCB groups reveals a clear and significant differentiation in their elemental compositions, a direct result of their specialized functions within the vehicle. A comparative overview of these groups is essential for developing an intelligent and efficient recycling strategy. The primary distinction lies in the distribution of the most economically significant metals: copper (Cu), a high-volume base metal, and precious metals like gold (Au), silver (Ag), and palladium (Pd).

The Power Electronics & HV Systems group stands apart as being overwhelmingly dominated by copper. With a typical weight percentage of 60%, these boards are the single richest source of copper among all electronic systems in a BEV. The mass of copper per unit area is also exceptionally high, typically around 25.0 mg/cm², reflecting the use of heavy copper layers and embedded busbars. Conversely, the concentration of precious metals in this group is the lowest of the five. This creates a distinct material profile: high in bulk commodity metal value but low in high-value, low-concentration precious metals.

At the other end of the spectrum are the Vehicle Control & Computing and the Infotainment & Communication groups. These boards have a much lower copper content, typically ranging from 35% to 40% by weight. Their value proposition for recycling is driven by their significantly higher concentrations of precious metals. The Infotainment & Communication boards, for example, show a typical gold concentration of 0.1 mg/cm² and a palladium concentration of 0.05 mg/cm², which are substantially higher than in power electronics. These boards are analogous to PCBs from high-end consumer electronics like computers and mobile phones, where the economic incentive for recycling is heavily weighted towards the recovery of gold, palladium, and silver [22, 34].

The Battery Management Systems (BMS) and Safety & Sensor Systems groups occupy a middle ground. The BMS PCBs have a high copper content (typically 50% by weight) due to their need to handle charging and discharging currents, but they also contain a moderate amount of precious metals associated with their complex monitoring and control circuitry. Safety & Sensor Systems have a moderate copper content (typically 40%) and a significant precious metal content, reflecting their need for ultra-reliable components and connectors.

This heterogeneity has profound implications for recycling. Treating all BEV PCBs as a single, homogenous waste stream would be highly inefficient. If boards are shredded and processed together, the high copper content from power electronics would dilute the concentration of precious metals from the computing and infotainment boards, making their recovery more difficult and less economically viable. For instance, the economic value of recyclable precious metals in one ton of general waste PCBs can be over $2,000, with gold accounting for up to 98% of this value [21]. Failing to isolate the boards where this gold is concentrated represents a significant lost opportunity. Therefore, the data strongly supports a recycling model that begins with the sorting of PCBs based on their functional group of origin. This would allow for the creation of at least two primary streams: a high-copper stream from power electronics, and a high-precious-metal stream from control, computing, and infotainment boards.

### **5. Implications for Recycling and Resource Recovery**

The detailed elemental characterization of BEV Printed Circuit Boards provides a critical foundation for designing and implementing advanced, economically viable, and environmentally responsible recycling processes. The inherent heterogeneity of these boards is not a mere academic observation; it is the central challenge and opportunity for the e-waste recycling industry. A generic approach to recycling, where all PCBs are shredded and processed collectively, is fundamentally flawed and will fail to maximize resource recovery. The findings of this report point toward a more sophisticated, multi-stream strategy.

Generally, waste PCBs are composed of approximately 40% metals, 30% organic materials (such as epoxy resins and flame retardants), and 30% ceramics (primarily glass fibers from the substrate) [17, 18]. The primary goal of recycling is to separate and recover the valuable metallic fraction while safely managing the non-metallic and potentially hazardous components. The economic drivers are powerful; the concentration of precious metals like gold in PCBs can be ten times higher than in rich mineral ores, making them a lucrative "urban mine" [21]. Furthermore, recycling metals consumes substantially less energy and produces fewer greenhouse gas emissions than mining and refining virgin materials.

The main technological pathways for metal recovery from PCBs include pre-treatment, pyrometallurgy, and hydrometallurgy [19]. Pre-treatment involves dismantling components and then shredding or crushing the boards to liberate the materials. This is followed by mechanical separation techniques based on density, magnetism, and electrostatic properties. Pyrometallurgy uses high temperatures (1400-1600 °C) in a smelter to burn off the organic fraction and melt the metals, with copper acting as a collector for precious metals [17, 19]. This method is robust and effective for high-volume processing but can generate harmful emissions if not properly controlled. Hydrometallurgy uses aqueous chemical solutions, such as acids (nitric acid, sulfuric acid) or other lixiviants, to selectively dissolve metals from the crushed material [17, 19]. These dissolved metals are then recovered through processes like precipitation or electrowinning. Hydrometallurgy can achieve high purity and selectivity but involves the use of corrosive chemicals and requires careful wastewater treatment.

The compositional differences identified in this report allow for the strategic application of these technologies. The high-copper, low-precious-metal PCBs from the Power Electronics & HV Systems group are ideal candidates for a pyrometallurgical process. Their high copper content makes them an excellent feed for a copper smelter, which can efficiently recover the copper, tin, lead, and the small amounts of silver present. Sending these boards to a hydrometallurgical process designed for precious metals would be inefficient, as the large volume of copper would consume a disproportionate amount of expensive chemical reagents.

Conversely, the PCBs from the Vehicle Control, Infotainment, and Safety Systems are prime candidates for a dedicated precious metal recovery stream, likely centered on hydrometallurgical techniques. Their higher concentrations of gold, palladium, and silver make the use of more precise and targeted chemical leaching processes economically justifiable. By pre-sorting and directing these boards to a specialized circuit, the concentration of precious metals in the feed material is kept high, maximizing the efficiency and yield of the recovery process. The challenge of analytical variability, where different chemical analysis methods can produce significantly different results for precious and hazardous metals, also highlights the need for robust quality assurance in any recycling operation to accurately assess the value of incoming material streams [2].

Finally, the non-metallic fraction, consisting of resins and glass fibers, which can constitute up to 70% of the PCB's mass, must also be managed [20]. Historically, this fraction was often landfilled or incinerated. However, there is growing research into repurposing this material as a filler or reinforcement in composites and construction materials, creating a more fully circular solution. The end-of-life vehicle recycling ecosystem also produces Automotive Shredder Residue (ASR), the non-metallic fluff left after a car is shredded [32]. Properly managing and recycling PCBs prevents these valuable and sometimes hazardous materials from ending up in the ASR stream, which is difficult and costly to process.

### **6. Conclusion**

This report has established that the Printed Circuit Boards within a Battery Electric Vehicle are not a monolithic entity but a diverse collection of components with highly distinct elemental compositions. By categorizing BEV PCBs into five functional groups—Power Electronics & HV Systems, Battery Management Systems, Vehicle Control & Computing, Infotainment & Communication, and Safety & Sensor Systems—we have demonstrated significant and predictable variations in their material makeup. The key finding is the clear demarcation between boards dominated by high concentrations of copper, such as those in power electronics, and those characterized by elevated levels of precious metals like gold and palladium, found in computing, control, and infotainment systems.

This compositional heterogeneity is the single most important factor for the development of an effective recycling strategy. The data presented unequivocally argues against a commingled, one-size-fits-all recycling process. Such an approach would lead to the dilution of valuable materials, reduced recovery efficiencies, and suboptimal economic returns. Instead, the findings provide a clear rationale for a sophisticated, multi-stream recycling model predicated on the pre-sorting of PCBs according to their functional origin.

For the technical team tasked with developing this model, this report offers a foundational dataset. The detailed tables of elemental concentrations provide the quantitative basis for modeling material flows, estimating the potential economic value of different streams, and selecting the most appropriate recycling technologies for each. By directing high-copper boards to pyrometallurgical pathways and high-precious-metal boards to specialized hydrometallurgical circuits, a future recycling facility can optimize its operations for both efficiency and profitability. Ultimately, leveraging this detailed understanding of PCB composition will be essential for unlocking the full value of end-of-life BEVs and building a truly circular economy for the automotive electronics of the future.

# References
1. [Characteristics and aging of PCB embedded power electronics - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S002627141500164X)
2. [Multi-element chemical analysis of printed circuit boards – challenges and pitfalls - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0956053X19302922)
3. [Novel Approach Unveils Elemental Composition and Properties of Recycled Printed-Circuit Board (PCB) Powder | Spectroscopy Online](https://www.spectroscopyonline.com/view/novel-approach-unveils-elemental-composition-and-properties-of-recycled-printed-circuit-board-pcb-powder)
4. [Automotive PCB Design Guidelines: Build Robust Circuits for EVs, Hybrids, and ICE Vehicles - One-stop Solution for PCB design, Manufacturing and Assembly& Reverse Engineering. - IWDF Solutions](https://iwdfsolutions.com/automotive-pcb-design-guidelines/)
5. [Detailed description of inverter PCB - JunchiPower](https://www.junchipower.com/detailed-description-of-inverter-pcb/)
6. [Automotive inverter PCB boards: a comprehensive guide - SpringerLink](https://link.springer.com/article/10.1007/s11367-018-1491-3)
7. [What is an Inverter PCB Board? - Kingsun PCB](https://www.kingsunpcb.com/what-is-an-inverter-pcb-board/)
8. [Inverter PCB - Hillman Curtis](https://hillmancurtis.com/inverter-pcb/)
9. [Lithium-ion Battery Management and Protection Module (BMS) Teardown, Schematics, Parts List and Working - Circuit Digest](https://circuitdigest.com/electronic-circuits/lithium-ion-battery-management-and-protection-module-bms-teardown-schematics-parts-list-and-working)
10. [BMS (Battery Management System) - Grepow](https://www.grepow.com/technology/bms.html)
11. [BMS PCB: The Ultimate Guide - JarnisTech](https://www.jarnistech.com/bms-pcb)
12. [BMS PCB Design: The Ultimate Guide - PCBSync](https://pcbsync.com/bms-pcb-design/)
13. [What is a BMS PCB Board? - Kingsun PCB](https://www.kingsunpcb.com/what-is-a-bms-pcb-board/)
14. [ECU PCB Testing and Validation: Ensuring Automotive Standards - AllPCB](https://www.allpcb.com/blog/pcb-knowledge/ecu-pcb-testing-and-validation-ensuring-automotive-standards.html)
15. [Electronic Control Unit - an overview | ScienceDirect Topics - ScienceDirect](https://www.sciencedirect.com/topics/computer-science/electronic-control-unit)
16. [Automotive PCB Properties and Design Considerations - Technical Articles - EEPower](https://eepower.com/technical-articles/automotive-pcb-properties-and-design-considerations/)
17. [The PCB Recycling Process in Design and Electronics Production - Cadence](https://resources.pcb.cadence.com/blog/2020-the-pcb-recycling-process-in-design-and-electronics-production)
18. [Understanding PCB Recycling - Genox](https://www.genoxtech.com/en/news_i_understanding-pcb-recycling.html)
19. [Printed Circuit Boards (PCBs) Waste Recycling Technologies - IntechOpen](https://www.intechopen.com/chapters/18491)
20. [Recycling of non-metallic fractions of waste printed circuit boards (WPCBs): A review - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0921344921006352)
21. [Assessment of Precious Metals Positioning in Waste Printed Circuit Boards and the Economic Benefits of Recycling - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0956053X21006759)
22. [Comprehensive characterization of printed circuit boards of various end-of-life electrical and electronic equipment for beneficiation investigation - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0956053X18300801)
23. [Dynamic material flow analysis of critical metals in lithium-ion batteries for electric vehicles in China - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0956053X23006037)
24. [Material Flow Analysis of Critical Raw Materials for Lithium-Ion Batteries in Germany - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9972231/)
25. [Future material demand for automotive lithium-based batteries - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0360544220316406?casa_token=jF_vGhxnFZMAAAAA:gnnxxrFXIEiiX4g3lM2IiSto_o7Xbjvqwzbd-mtSq1V2GFmhWz4iW9AtqJx0lJNUvaE8HRgvuA)
26. [Dynamic material flow analysis of lithium and cobalt in mainland China, 2000–2018 - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0921344920304390)
27. [Precious Metals In Cars - US Gold Bureau](https://www.usgoldbureau.com/news/post/precious-metals-in-cars-everything-to-know)
28. [Automotive PCB Design Guidelines: Build Robust Circuits for EVs, Hybrids, and ICE Vehicles - IWDF Solutions](https://iwdfsolutions.com/automotive-pcb-design-guidelines/)
29. [In-Depth Overview of Automotive Electronic PCB - LST PCB](https://www.lstpcb.com/news/in-depth-overview-of-automotive-electronic-pcb/)
30. [Automotive-Grade Chips: A Comprehensive Guide for PCB Design and Manufacturing - SYS Technology Co., Ltd.](https://www.syspcb.com/pcb-blog/knowledge/automotive-grade-chips-a-comprehensive-guide-for-pcb-design-and-manufacturing.html)
31. [Automotive PCB Properties and Design Considerations - EE Power](https://eepower.com/technical-articles/automotive-pcb-properties-and-design-considerations/)
32. [automotive shredder residue - Science.gov](https://www.science.gov/topicpages/a/automotive+shredder+residue.html)
33. [Metals Content in Printed Circuit Board Waste - ResearchGate](https://www.researchgate.net/publication/298315369_Metals_Content_in_Printed_Circuit_Board_Waste)
34. [Comprehensive characterization of printed circuit boards of various end-of-life electrical and electronic equipment for beneficiation investigation - ResearchGate](https://www.researchgate.net/publication/323180809_Comprehensive_characterization_of_printed_circuit_boards_of_various_end-of-life_electrical_and_electronic_equipment_for_beneficiation_investigation)
### **6. Matrix Lighting & Illumination Systems**

Matrix Lighting & Illumination Systems represent a rapidly advancing area of automotive electronics, critical for modern BEV safety and user experience. These systems, particularly prevalent in D-F segment vehicles, include adaptive LED matrix headlights, dynamic rear lighting arrays, and sophisticated ambient lighting controls. The PCBs in this group are engineered for high-power LED applications, demanding exceptional thermal management and component density.

**Technical Specifications:**
- **Layer Count:** Typically 2 to 4 layers, often utilizing a rigid-flex or HDI design to accommodate complex geometries within lighting assemblies.
- **Typical Dimensions:** Variable, ranging from small modules (5cm x 5cm) for ambient lighting to larger, complex shapes for headlight arrays (e.g., 15cm x 25cm).
- **Substrate Materials:** Primarily aluminum or copper-based PCBs (MCPCBs) for superior thermal conductivity (>1.0 W/m·K for aluminum, >380 W/m·K for copper). Ceramic substrates may be used in the most demanding high-power applications.
- **Surface Finish:** Commonly lead-free HASL, ENIG (Immersion Gold), or OSP for corrosion resistance and reliable solder connections.

**Elemental Composition:**
Lighting PCBs are characterized by a high copper and aluminum content to manage the significant heat generated by high-intensity LEDs. The use of precious metals like gold and palladium is moderate, concentrated in control circuitry and connectors.

| Element | Weight per Unit Area (mg/cm²) | Percentage by Weight (%) |
| :--- | :--- | :--- |
| | **Min - Typ - Max** | **Min - Typ - Max** |
| **Cu** | 20.0 - 30.0 - 45.0 | 55.0 - 65.0 - 75.0 |
| **Ag** | 0.08 - 0.25 - 0.5 | 0.2 - 0.4 - 0.8 |
| **Au** | 0.02 - 0.04 - 0.06 | 0.04 - 0.06 - 0.1 |
| **Sn** | 1.2 - 2.8 - 4.5 | 3.5 - 4.5 - 5.5 |
| **Pb** | 0.0 - 0.1 - 0.3 | 0.0 - 0.2 - 0.5 |
| **Ni** | 0.3 - 0.6 - 1.1 | 0.8 - 1.2 - 2.0 |
| **Pd** | 0.008 - 0.015 - 0.025 | 0.02 - 0.03 - 0.06 |
| **Al** | 5.0 - 10.0 - 18.0 | 10.0 - 15.0 - 20.0 |
| **Zn** | 0.15 - 0.25 - 0.55 | 0.3 - 0.5 - 0.9 |
| **Fe** | 1.5 - 3.5 - 5.5 | 3.5 - 5.5 - 8.5 |

**Recycling Considerations:**
The high concentration of copper and aluminum makes these boards attractive for metallurgical recycling. However, the complex, multi-material construction, including lenses, heat sinks, and various plastics, requires sophisticated dismantling and sorting processes. The presence of valuable precious metals, though in smaller quantities than in computing boards, justifies their recovery through specialized hydrometallurgical processes. The increasing use of vitrimer-based PCBs in research presents a future opportunity for more efficient and environmentally friendly recycling.

