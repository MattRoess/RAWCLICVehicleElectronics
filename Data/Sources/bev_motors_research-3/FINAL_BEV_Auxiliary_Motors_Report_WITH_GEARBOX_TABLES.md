# Comprehensive Analysis of Auxiliary Electric Motors and Integrated Gearboxes in European and Asian Battery Electric Vehicles (2024-2026 Models)

**Report Date:** 2026-03-11

## Executive Summary

This report presents a comprehensive technical, quantitative, and supply chain analysis of non-drivetrain auxiliary electric motors and their integrated gearboxes in Battery Electric Vehicles (BEVs) projected for the European market for the 2024-2026 model years. The research focuses on three distinct motor categories, now updated to reflect their specific roles in modern vehicle architectures: small stepper motors with a power rating under 50 watts, medium DC motors rated between 50 and 500 watts, and medium stepper motors with a power rating of 50 to 200 watts. The increasing sophistication of comfort, safety, and thermal management systems in BEVs has driven a significant proliferation in the number and complexity of these motors. They perform critical functions ranging from passenger cabin climate control and power seat adjustment to the essential thermal management of the high-voltage battery and power electronics, and the precise actuation of advanced driver-assistance and aerodynamic systems.

A critical finding of this updated analysis is the indispensable role of gearboxes in modulating the speed and torque of these auxiliary motors. For the majority of auxiliary functions that require high torque at low operational speeds—such as moving a seat, lifting a window, or adjusting a mirror—geared motors are the prevalent and most practical solution. The integration of a gearbox allows for the use of smaller, lighter, and more energy-efficient motors to perform tasks that would otherwise require much larger and more power-intensive direct-drive units. The most common gearbox types are planetary systems, favored for their high torque density and compact design in applications like power seats; worm gear systems, valued for their high reduction ratios and inherent self-locking capability in window regulators; and spur gear systems, used in less demanding, cost-sensitive applications.

This updated analysis properly distinguishes and allocates applications between motor categories. Small stepper motors are primarily utilized for lower-force, high-precision tasks such as the majority of HVAC blend door actuators [105, 106]. Medium DC motors are the workhorses for continuous power and high-force applications, including coolant pumps, window lifts, and seat adjustment mechanisms [88, 93]. Crucially, this report now identifies and details the significant role of medium stepper motors, which are now understood to comprise approximately 20% of the medium-power auxiliary motor segment. These motors are predominantly used in applications requiring a combination of precision and higher force, such as active grille shutters, adaptive headlamp leveling and swiveling systems, and charging port door actuators [109, 113, 118].

The report further provides a detailed quantitative breakdown of motor counts across six vehicle segments, from A-segment mini cars to F-segment luxury vehicles, revealing a direct correlation between a vehicle's market position and its auxiliary motor content. A-segment vehicles may contain as few as 10 motors, while high-end F-segment models can feature over 80 individual auxiliary motor assemblies.

Finally, the analysis delves into the material composition, cost structures, and supply chain dynamics for each motor-gearbox assembly. Key materials such as copper, electrical steel, aluminum, permanent magnets, and specialized gearbox materials like alloy steels and engineering plastics (POM, PA66) are examined. The report highlights the critical influence of raw material costs, particularly the volatile prices of copper and Neodymium Iron Boron (NdFeB) rare earth magnets, on the overall cost of these components [74, 98]. A significant finding is the automotive industry's profound supply chain vulnerability stemming from its dependence on China for the mining, processing, and manufacturing of rare earth magnets [81]. In response, global automakers and governments are actively pursuing risk mitigation strategies, including supply chain diversification, vertical integration, and research into alternative motor technologies, to secure the future of electric mobility [81, 84].

## Introduction

The automotive industry's paradigm shift towards battery electric vehicles (BEVs) encompasses a transformation that extends far beyond the primary propulsion system. A fundamental, yet frequently underestimated, aspect of this evolution is the comprehensive electrification of auxiliary vehicle systems. In a BEV, every function that once drew mechanical, hydraulic, or vacuum power from a running internal combustion engine must now be powered by a dedicated electric motor. This necessity has led to the integration of a vast and diverse array of small and medium-sized electric motors, which are now responsible for a spectrum of functions essential to vehicle safety, passenger comfort, operational efficiency, and brand differentiation [88, 93]. The energy consumed by these numerous auxiliary systems has a direct and measurable impact on the vehicle's overall driving range, elevating the efficiency, weight, and control of their motors to a position of critical importance for automotive engineers and designers.

A key component in optimizing the performance of these motors is the gearbox. Most auxiliary applications require low-speed, high-torque motion—a characteristic that is often the opposite of a small electric motor's native output, which is typically high-speed and low-torque. A gearbox acts as a mechanical torque converter, reducing the motor's rotational speed while proportionally increasing its output torque. This allows for the use of smaller, lighter, and more energy-efficient motors to perform tasks that would otherwise require much larger, heavier, and more power-intensive direct-drive units. The selection of the gearbox type—be it planetary, worm, or spur—and its specific gear ratio is a critical engineering decision that tailors the motor's performance to the demands of each function, from the high-torque, self-locking action needed for a window regulator to the compact, high-force output required for a power seat.

This report delivers an in-depth investigation into these auxiliary motor and gearbox assemblies, specifically within the context of European and Asian BEV models anticipated for sale in the European market for the 2024-2026 model years. The analysis has been updated and structured around three precisely defined motor classifications to reflect the latest understanding of their application within the vehicle architecture: small stepper motors (<50W), medium DC motors (50-500W), and medium stepper motors (50-200W). For each of these distinct categories, this report provides a detailed examination of their specific applications, typical in-vehicle locations, core technical characteristics, and representative power ratings, now including detailed information on their integrated gearboxes. By synthesizing and expanding upon information from technical reviews, component specifications, industry publications, and market analysis, this document provides an authoritative and holistic overview for stakeholders seeking to understand the component-level architecture, quantitative distribution, and material supply chain of modern electric vehicles. This updated framework, which now correctly identifies the significant role of medium stepper motors and their associated gear systems, offers a more accurate and nuanced perspective on the intricate electromechanical ecosystem that defines the contemporary BEV.

## Part 1: Technical Analysis of Auxiliary Motor Applications

The functionality of a modern BEV is supported by a distributed network of electric motors, each selected for its unique performance characteristics and often paired with a specific gearbox to meet the application's requirements. This section provides a detailed technical analysis of the three primary categories of auxiliary motors, outlining their core principles, key applications, and the engineering rationale for their deployment in specific vehicle systems. The updated analysis correctly attributes applications to each motor type and integrates the critical role of the gearbox, providing a clearer picture of the division of labor within the vehicle's electromechanical architecture.

### Small Stepper Motors (<50 Watts)

Small stepper motors, characterized by power ratings typically below 50 watts, are foundational components for a multitude of precision control systems in modern BEVs. Their defining operational characteristic is the ability to rotate in discrete, fixed angular increments, known as "steps" [2, 4]. This allows for exceptionally accurate positioning of mechanical components without the need for complex and costly closed-loop feedback systems involving sensors like encoders or resolvers [3]. This principle, known as **open-loop control**, makes them remarkably reliable and cost-effective for applications where exact positioning and repeatability are more critical than high rotational speed or substantial torque [3]. In the energy-conscious design of a BEV, where every watt of consumption can affect the overall driving range, the inherent efficiency and low standby power draw of these motors represent a significant engineering advantage. They are most commonly employed in systems that require the precise and repeatable positioning of components such as flaps, valves, and indicator needles [6]. Their control is typically managed by dedicated driver circuits or integrated into larger electronic control units (ECUs) that communicate over vehicle data networks like the Local Interconnect Network (LIN) bus, enabling sophisticated, coordinated, and diagnostic-capable operation across the vehicle.

One of the most prevalent and high-volume applications for small stepper motors is within the Heating, Ventilation, and Air Conditioning (HVAC) system [103, 105]. These motors function as the primary actuators, driving the various doors and flaps that control air temperature, distribution, and intake source. Located deep within the main HVAC module, which is typically situated behind the vehicle's dashboard and firewall, these actuators are critical for creating and maintaining a comfortable cabin environment for passengers. To generate sufficient force to move the doors against airflow pressure and hold them in specific positions, these small motors are almost always paired with a gearbox. These are typically simple spur or compact planetary gear trains, often made from engineering plastics like POM or PA66 for quiet operation and low cost. Gear ratios for these actuators are moderate to high, commonly in the range of 20:1 to 150:1, which translates the motor's precise steps into forceful, controlled linear or rotary motion of the door. A key function is the operation of the **blend door**, which regulates the final cabin temperature by precisely mixing hot air from the heater core with chilled air from the evaporator [105, 106]. A geared small stepper motor allows the vehicle's climate control unit to position this door with exceptional accuracy, enabling the system to achieve and maintain the exact temperature selected by the occupants. According to a 2019 review published by Transstellar Journals, the use of stepper motors in this role can reduce the energy consumption of the actuator system by as much as 20.15% compared to traditional DC motors, a vital energy saving in a BEV [106]. Beyond temperature regulation, these geared stepper motors also control the **mode doors**, which direct the flow of conditioned air to different cabin vents, and the **recirculation flap**, which switches the system's air intake [105]. The combination of a stepper motor and a gearbox ensures consistent, silent, and precise performance, allowing for complex climate control strategies.

Beyond HVAC systems, small stepper motors are also utilized in a variety of other low-power actuator roles throughout the vehicle. In some luxury vehicles, they are used for the automatic deployment and retraction of interior components, such as display screens or air vents that present themselves upon vehicle startup. Another application is within the instrument cluster itself, where small stepper motors are often used to drive the physical needles of analog-style gauges for speedometers, power-output meters, and state-of-charge indicators [6]. Their ability to move to and hold a precise position makes them ideal for providing clear and stable readings to the driver. Furthermore, in high-end E- and F-segment vehicles, the concept of automatic or powered doors may utilize small stepper motors for the latching and unlatching mechanisms, working in concert with larger DC motors that provide the primary force for opening and closing the door. In these applications, the stepper motor's role is one of precision locking and release, ensuring a secure and smooth operation. The power required for these slow, deliberate movements is minimal, placing these motors firmly in the small, sub-50-watt category.

### Medium DC Motors (50 - 500 Watts)

Medium-power Direct Current (DC) motors, and particularly their more advanced brushless (BLDC) variants, serve as the robust workhorses in BEV auxiliary systems that demand continuous operation, high rotational speed, and significantly more power than small actuators can deliver. This category, defined for this report as motors with a power rating between 50 and 500 watts, is essential for a wide range of fluid-pumping and mechanical actuation applications [88, 93]. Unlike stepper motors, which excel at precise positioning, DC motors are engineered for sustained rotational speed and torque. However, for most mechanical actuation tasks, the motor's native high-speed, low-torque output is unsuitable. Therefore, these motors are frequently integrated with gearboxes to create a geared motor assembly. The gearbox reduces the speed and multiplies the torque, enabling a compact motor to perform heavy-duty tasks.

The most significant and critical application for medium DC motors in BEVs is driving the **electric water pumps** that circulate liquid coolant throughout the vehicle's various thermal management loops. This is a notable exception where gearboxes are not used; these pumps are direct-drive, with the motor's impeller connected directly to the motor shaft to achieve the high flow rates required. A modern BEV architecture may feature multiple, independent cooling circuits for the battery, power electronics, and cabin climate system, each requiring one or more dedicated pumps. Analysis of electric pump specifications indicates that power ratings commonly fall squarely within the 50-500 watt range [28, 33]. For instance, data from Explorist.life on 12V systems shows that a pump drawing 7.5 amps consumes 90 watts, while other sources cite an average power consumption of 150 watts for a general-purpose water pump [123, 124].

In contrast, nearly all other medium DC motor applications rely on gearboxes. **Power window lifts**, one for each door, use a geared DC motor to provide the necessary torque to raise and lower the window glass. These systems typically employ a **worm gearbox**, which offers two critical advantages: a very high gear reduction ratio in a compact, 90-degree package, and an inherent self-locking capability. Ratios can be exceptionally high, sometimes exceeding 500:1, to generate the required lifting force from a small motor. The self-locking nature prevents the window from being forced down, providing security without an external brake. Similarly, the **windshield wiper system** relies on one or two powerful DC motors with a high-ratio worm gear or linkage system to drive the wiper arms with sufficient force.

The most extensive use of geared medium DC motors is in **power seats**. A basic 6-way adjustable seat uses three geared motors (for fore/aft, height, and recline), while an advanced 16-way massaging seat could contain a dozen or more [11, 16, 19]. These applications demand high torque to move the seat and occupant. **Planetary gearboxes** are commonly used for their high torque density and compact, concentric design, which fits well within the seat structure [14, 16]. Gear ratios for seat motors typically range from 20:1 to over 100:1, allowing a small DC motor to produce the substantial force needed. In higher-segment vehicles, features like **power-folding mirrors**, **power-adjustable steering columns**, and **power liftgates or trunks** all utilize geared medium DC motors, often with worm or planetary systems to achieve the required force and controlled motion [88].

### Medium Stepper Motors (50 - 200 Watts)

The category of medium stepper motors, with power ratings between 50 and 200 watts, represents a critical and increasingly prevalent segment within modern BEV auxiliary systems. This updated analysis corrects previous assumptions and recognizes that these motors are the preferred solution for applications that require the high precision of a stepper motor combined with a level of force or torque that exceeds the capabilities of their smaller, sub-50-watt counterparts. These motors are almost exclusively of the hybrid synchronous design, which provides an optimal balance of torque, resolution, and holding power [68, 69]. To achieve the necessary output force, these motors are almost always paired with a robust gearbox, typically a planetary or worm drive system. This combination allows for precise, controlled, and forceful movement, making them highly reliable and cost-effective for a range of advanced safety and efficiency systems.

A key application for geared medium stepper motors is in **adaptive and automatic headlamp systems**. Modern BEVs are frequently equipped with automatic headlamp leveling and Adaptive Front-lighting Systems (AFS), both of which rely on these motor assemblies for their precise and rapid adjustments [109, 112]. Housed directly within the headlamp assemblies, these actuators must move the entire projector and lens assembly quickly and accurately. European regulations mandate automatic headlamp leveling for high-intensity headlights to prevent dazzling oncoming drivers [108]. The system uses vehicle level sensors to command the geared stepper motors to make minute vertical adjustments. In more advanced AFS, stepper motors also provide horizontal, or swivel, adjustments [109, 112]. The force required necessitates a motor with more torque than a small stepper can provide, and a high-ratio planetary gearbox is often used to deliver this force in a compact package. Each headlamp in an advanced system can contain two or more of these geared motors, making them a significant contributor to the overall motor count in premium vehicles [111].

Another critical efficiency-related application is in **active grille shutters**. These systems, increasingly common on BEVs to optimize aerodynamic performance, feature motorized louvers in the front grille. The actuators that control these louvers must be robust enough to operate against significant air pressure at high vehicle speeds and must be watertight to withstand their exposed location [113]. A geared medium stepper motor, often using a planetary or worm gearbox, provides the ideal combination of precise positional control—allowing the shutters to be partially or fully opened to fine-tune cooling and drag—and the high torque required to ensure reliable operation under all conditions. By precisely controlling airflow, these systems directly contribute to optimizing the vehicle's energy consumption and extending its driving range.

Furthermore, medium stepper motors are the component of choice for **charging port door actuators**. This motorized mechanism is responsible for locking and unlocking the flap that covers the vehicle's charging port [118, 119]. The system must be highly reliable and provide a secure locking force. The action requires more force than a simple latch, needing to push the door open and pull it securely closed, often against ice or debris. A geared medium stepper motor provides the necessary torque and positional accuracy to ensure the door is either fully open or fully and securely latched, integrating with the vehicle's central locking system [121, 122]. In premium vehicles with dual charging ports (e.g., AC and DC), two such actuators may be present. The combination of these verified applications demonstrates that geared medium stepper motors are not a niche category, but rather an essential component class for enabling many of the advanced safety, efficiency, and convenience features that define the modern BEV.

## Part 2: Quantitative Analysis of Motor Distribution by Vehicle Segment

The number and type of auxiliary electric motors integrated into a Battery Electric Vehicle are not uniform across the market. Instead, the motor count serves as a direct proxy for a vehicle's market segment, luxury level, and feature content. As manufacturers seek to differentiate their offerings and provide enhanced comfort, convenience, and safety, the quantity of electrified functions—and thus, the number of motors—increases dramatically. This section provides a quantitative analysis of auxiliary motor distribution across six standard European vehicle segments, from the entry-level A-segment to the flagship F-segment. The data presented is based on the updated understanding of motor applications, correctly allocating functions to small stepper, medium DC, and medium stepper motors, and provides a clear picture of the proliferation of these components as one moves up the automotive value chain.

The following tables summarize the estimated distribution of auxiliary motors. Table 1 provides a detailed breakdown of motor types, their associated gearboxes, and typical gear ratios used in specific vehicle systems, with estimated counts across the different segments. Table 2 provides a summarized total count for each motor category per segment and an estimate of the percentage of motors that are integrated with a gearbox, offering a clear overview of the overall trend. These estimates are derived from documented features of representative vehicles and the typical motorization and gearing strategies employed for those features.

### TABLE 1: Comprehensive Auxiliary Motor Distribution by System and Vehicle Segment (2024-2026)

| System/Application | Motor Type | Gearbox Type | Typical Gear Ratio | A-segment | B-segment | C-segment | D-segment | E-segment | F-segment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HVAC System** | Small Stepper | Spur/Planetary | 20:1 - 150:1 | 4-6 | 4-6 | 6-8 | 6-8 | 8-12 | 10-15 |
| **Headlamp System** | Medium Stepper | Planetary | 50:1 - 200:1 | 2 | 2 | 2-4 | 4 | 4-6 | 6-8 |
| **Active Grille Shutter** | Medium Stepper | Planetary/Worm | 50:1 - 200:1 | 0-1 | 1-2 | 1-2 | 2 | 2-4 | 4-6 |
| **Charging Port Lock(s)** | Medium Stepper | Planetary/Worm | 50:1 - 150:1 | 1 | 1 | 1 | 1-2 | 2 | 2 |
| **Automatic/Powered Doors** | Small Stepper | Spur/Planetary | 20:1 - 100:1 | 0 | 0 | 0 | 0 | 0-4 | 4 |
| **Window Lifts** | Medium DC | Worm | 50:1 - 2000:1 | 2 | 4 | 4 | 4 | 4 | 4 |
| **Windshield Wipers** | Medium DC | Worm/Linkage | 50:1 - 150:1 | 1-2 | 1-2 | 1-2 | 2 | 2 | 2 |
| **Coolant Pumps** | Medium DC | None | N/A | 1 | 1 | 1-2 | 2 | 2-3 | 3-4 |
| **Power Folding Mirrors** | Medium DC | Spur/Planetary | 100:1 - 200:1 | 0 | 2 | 2 | 2 | 2 | 2 |
| **Power Seats (per seat)** | Medium DC | Planetary/Worm | 20:1 - 100:1+ | 0 | 0 | 2-4 | 4-6 | 5-8 | 8-12 |
| **Total Power Seats** | Medium DC | Planetary/Worm | 20:1 - 100:1+ | 0 | 0 | 4-8 | 8-12 | 10-16 | 16-24 |
| **Sunroof/Panoramic Roof** | Medium DC | Worm/Planetary | 50:1 - 150:1 | 0 | 0 | 1-2 | 2 | 2 | 2-4 |
| **Power Liftgate/Trunk** | Medium DC | Worm/Planetary | 50:1 - 150:1 | 0 | 0 | 0 | 2 | 2 | 2 |
| **Soft-Close Doors** | Medium DC | Worm | 50:1 - 150:1 | 0 | 0 | 0 | 0-4 | 4 | 4 |
| **Power Steering Column** | Medium DC | Planetary | 50:1 - 150:1 | 0 | 0 | 0 | 0 | 2 | 2 |
| **Deployable Door Handles** | Medium DC | Planetary | 50:1 - 150:1 | 0 | 0 | 0 | 0 | 4 | 4 |

### TABLE 2: Summary of Total Estimated Auxiliary Motor Counts per Vehicle Segment

| Segment | Small Stepper Motors | Medium DC Motors | Medium Stepper Motors | Total Motors (Range) | Motors with Gearboxes (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A-segment** | 4-6 | 3-4 | 3-4 | **10-14** | 90% - 93% |
| **B-segment** | 4-6 | 7-8 | 4-5 | **15-19** | 93% - 95% |
| **C-segment** | 6-8 | 8-14 | 4-7 | **18-29** | 90% - 94% |
| **D-segment** | 6-8 | 14-20 | 7-8 | **27-36** | 93% - 95% |
| **E-segment** | 8-16 | 22-35 | 8-12 | **38-63** | 94% - 96% |
| **F-segment** | 10-19 | 31-46 | 12-16 | **53-81** | 94% - 96% |

### Analysis of Motor Distribution Across Segments

The data clearly illustrates a steep and consistent increase in auxiliary motor content as vehicle size, price, and feature complexity grow. A key insight from the updated data is the high prevalence of gearboxes across all segments; the vast majority of auxiliary motors, with the notable exception of direct-drive coolant pumps, are part of a geared assembly.

In the **A-Segment**, representing mini cars like the Fiat 500e, the total motor count ranges from 10 to 14 units. The thermal management system is typically simpler, requiring only a single direct-drive medium DC coolant pump. The remaining 9 to 13 motors are all geared. This includes a basic HVAC system with 4-6 geared small stepper motors, two geared medium DC motors for the front window lifts, and one or two for the wipers. Critically, even these basic vehicles require geared medium stepper motors for mandatory functions like headlamp leveling (2 units) and the charging port lock (1 unit). This establishes that over 90% of auxiliary motors in even the most basic BEVs rely on a gearbox.

Moving to the **B-Segment**, which includes popular small cars like the VW ID.3 and Peugeot e-208, the total motor count rises to a range of 15 to 19. The primary increase comes from the addition of geared medium DC motors. These models typically feature four power windows instead of two, and often include power-folding mirrors, adding four more geared DC motors. The count of geared medium stepper motors also begins to climb with the more frequent inclusion of active grille shutters (1-2 units). With the number of direct-drive coolant pumps remaining at one, the percentage of geared motors increases slightly to the 93-95% range.

The **C-Segment**, or compact car class, which includes high-volume models like the Tesla Model 3 and Nissan Ariya, marks a significant inflection point. The total motor count expands to a range of 18 to 29. Here, we see the introduction of optional power seats, which can add 4 to 8 geared medium DC motors. Dual-zone climate control becomes more prevalent, increasing the number of geared small stepper motors to between 6 and 8. More advanced adaptive lighting can increase the geared medium stepper motor count to 4. The potential inclusion of a motorized sunroof adds another one or two geared medium DC motors. While more complex thermal systems might add a second coolant pump, the proliferation of comfort features ensures the proportion of geared motors remains high.

In the **D-Segment** of mid-size cars, represented by models like the BMW i4 and Polestar 2, high-end features become more standard. The total motor count climbs to between 27 and 36. The most significant jump is in geared medium DC motors, driven by the standardization of more advanced power seats (adding up to 12 motors) and power liftgates (adding 2 motors). The geared medium stepper motor count also solidifies with advanced adaptive headlamps (4 units) and more complex active grille shutters (2 units). The number of direct-drive coolant pumps may increase to two, but this is far outpaced by the addition of numerous geared actuators, keeping the geared motor percentage around 94%.

The **E-Segment** and **F-Segment** represent the executive and luxury classes, respectively, with models like the Mercedes EQS, BMW iX, and Porsche Taycan. Here, the proliferation of motors is most extreme, with total counts reaching 53 to 81 motors or more. The number of geared small steppers grows to accommodate complex 4- or 5-zone climate control systems. The count of geared medium DC motors explodes due to features like 16- or 24-way executive rear seats with massage, panoramic sunroofs, soft-close doors, and deployable door handles—all of which use geared motors. The geared medium stepper motor count also reaches its peak with the most advanced adaptive headlamp and aerodynamic systems. Even with more complex thermal management systems requiring 3 or 4 direct-drive coolant pumps, the sheer volume of geared comfort and convenience motors ensures that the percentage of motors with gearboxes remains at its peak, around 94-96%.

## Part 3: Material Composition and Supply Chain Analysis

The performance, cost, and availability of auxiliary electric motors are fundamentally tied to the materials from which they are constructed and the global supply chains that provide them. This section delves into the specific material composition, weight, critical alloys, cost structures, and supply chain dynamics for each of the three motor categories. The analysis reveals a complex interplay between material science, manufacturing economics, and significant geopolitical risks, particularly concerning the sourcing of critical raw materials like copper and rare earth elements.

### Small Stepper Motors (<50W)

Small stepper motors are marvels of electromechanical precision, and their construction reflects a focus on achieving accurate motion in a compact and cost-effective package. Their material composition is a carefully balanced selection of metals, magnets, and plastics. The stationary part of the motor, the stator, is built around a core of laminated electrical steel, which is then wound with high-purity copper wire [4]. These copper coils generate the precise magnetic fields that drive the motor's step-by-step rotation. The rotating part, or rotor, defines the motor's type. In a simple Permanent Magnet (PM) stepper, the rotor is a magnetized cylinder of high-retentive steel [1, 4]. In a Variable Reluctance (VR) stepper, it is a toothed rotor made of soft iron [1, 4, 5]. However, the most common type in demanding automotive applications is the Hybrid stepper, which features a complex rotor with a permanently magnetized core, often using powerful rare earth magnets, encased in toothed soft iron cups [1, 4, 5]. The motor's housing and structural components often utilize engineering plastics and aluminum to reduce weight and provide environmental protection. The weight of these small motors is typically low, with an estimated range of 0.2 kg to 0.4 kg, depending on the design and torque requirements [7, 8, 10, 11].

The performance of these motors is critically dependent on specialized alloys and magnet grades. The stator core is made from **non-grain oriented electrical steel (NOES)**, such as grades M19, M27, or M36 silicon steel [22, 25]. These grades are isotropic, meaning their magnetic properties are uniform in all directions, which is essential for the rotating magnetic fields in a motor [23, 25]. Thinner laminations, typically 0.20 mm to 0.35 mm, are used to minimize energy losses from eddy currents at higher operating frequencies [21, 22]. For high-performance hybrid steppers, the magnet of choice is a sintered **Neodymium Iron Boron (NdFeB)** magnet [28, 30]. These rare earth magnets offer the highest magnetic energy density available, enabling high torque in a small package [31, 33]. The specific grade, such as N48SH or N45UH, is critical [29, 31]. The number indicates magnetic strength, while the letters denote the maximum operating temperature. Automotive applications, with their harsh thermal environments, demand high-temperature grades (SH, UH, EH series, rated for 150°C to 200°C) to prevent irreversible demagnetization [29].

The cost structure of small stepper motors is heavily influenced by raw material prices and manufacturing volume. The most significant cost drivers are the copper for the windings and, for hybrid motors, the NdFeB magnet. Historical analysis shows that the magnet alone can account for a very large percentage of the total material cost, making the motor's price highly sensitive to the volatile rare earth market [74]. Copper prices, which are also subject to significant global market fluctuations, represent another major variable cost [98, 100]. Manufacturing complexity, especially the intricate assembly of a hybrid rotor, also adds to the cost. The supply chain for these motors is global, with major manufacturers like Nidec Corporation and Johnson Electric operating production facilities worldwide [89, 90, 92]. However, this supply chain has a critical vulnerability: its overwhelming dependence on China, which controls approximately 90% of the global production of finished NdFeB magnets [81]. This concentration of supply creates a significant risk of price shocks and disruptions due to geopolitical factors. In response, automakers and governments are actively pursuing strategies to de-risk this dependency, including diversifying suppliers, investing in non-Chinese mining and processing operations, and funding research into rare-earth-free motor technologies [81].

### Medium DC Motors (50-500W)

Medium DC motors are built for power and durability, and their material composition reflects this purpose. These motors are dominated by metals, with housings frequently constructed from die-cast **aluminum** for its excellent balance of low weight and high thermal conductivity, allowing the casing to act as an effective heat sink [53, 55]. In more rugged applications, **steel** may be used for the housing [53]. The electrical windings are universally made from **100% copper wire** to efficiently handle the higher currents required for this power class [48, 50]. The internal construction varies between brushed and brushless (BLDC) designs. Traditional brushed motors often use cost-effective **ferrite permanent magnets** in the stator, with the copper windings on the rotor [60, 62]. In contrast, high-performance BLDC motors typically place stronger **NdFeB rare earth magnets** on the rotor to achieve higher torque density and efficiency, with the windings in the stator [63, 65]. The weight of these motors is substantial, reflecting their power output. A 200W DC motor, for example, can weigh between 2.3 kg and 3.6 kg [41, 42, 43, 44, 45]. Copper content is significant, estimated to be between 15% and 18% of the total motor weight, with the remainder composed of steel, aluminum, and magnetic materials [13, 15].

The specific alloys and magnet grades are chosen to balance performance, cost, and longevity. The motor shaft, which transmits the mechanical power, is made from high-strength steel, such as **SAE 1045** carbon steel or, for more demanding applications, **4140** chrome-molybdenum alloy steel [57, 58]. The choice of magnet material represents a key engineering trade-off. **Ferrite magnets**, made from iron oxide and strontium carbonate, are inexpensive and highly resistant to high temperatures and corrosion, making them suitable for cost-sensitive applications where maximum power density is not the primary goal [60, 64]. For high-performance applications, however, **Neodymium (NdFeB) magnets** are preferred. They offer unmatched magnetic strength, enabling smaller, lighter, and more efficient motors, which is a critical advantage in BEVs [61, 65]. However, they are more expensive and require high-coercivity grades (e.g., SH, UH series) to withstand the high operating temperatures found in automotive environments without demagnetizing [60, 61].

The cost of medium DC motors is driven by this material selection. A high-performance BLDC motor using NdFeB magnets is significantly more expensive than a traditional brushed motor using ferrites, due to both the magnet cost and the required electronic controller [74]. The price of copper is a major factor; with a high copper content by weight, these motors are highly exposed to fluctuations in the copper market, which has seen sustained price increases due to global electrification demand [97, 99]. The supply chain for these motors is dominated by major Tier 1 automotive suppliers like Robert Bosch GmbH, Denso Corporation, and Continental AG [88, 90, 92]. These global giants operate extensive manufacturing networks to serve automakers regionally. While the copper supply chain presents challenges of price volatility, the most acute risk for high-performance BLDC motors is the same as for steppers: the dependence on the Chinese-controlled rare earth magnet supply chain [81]. The larger mass of magnetic material required for these more powerful motors makes this dependency even more significant, reinforcing the strategic imperative for the industry to diversify its sourcing of these critical materials.

### Medium Stepper Motors (50-200W)

Medium stepper motors, which bridge the gap between low-force precision and high-power continuous motion, are constructed with materials designed to handle higher torque and thermal loads. Their material composition is an scaled-up version of the small hybrid stepper. The stator consists of a larger stack of electrical steel laminations and more substantial **copper windings** to carry the increased current needed for the 50-200W power rating [68, 70]. The rotor is a more robust hybrid design, featuring a powerful **sintered NdFeB permanent magnet** core to generate the high torque characteristic of this class [68, 69]. The housing is typically a rigid metal structure, often made of aluminum or steel, to provide structural support and manage heat dissipation. For applications requiring even higher force, these motors are often paired with a planetary gearbox, which introduces additional materials like **powder metallurgy** or machined **alloy steel** for the gears [70, 71]. The weight of these motors is considerably greater than their smaller counterparts, with an estimated range of 0.7 kg to 1.5 kg or more, especially for geared versions.

The alloys and magnet grades used in medium stepper motors are selected to maximize performance under higher stress. The stator laminations are made from high-quality **non-grain oriented electrical steel (NOES)**, with grades like M27 or M36 and thin gauges (0.35mm or less) being preferred to minimize core losses and improve efficiency under higher loads [22, 25]. The permanent magnet is the most critical component for performance. To produce the required torque and resist demagnetization from strong magnetic fields and high operating temperatures, high-strength, high-coercivity **NdFeB magnet grades** are essential [28, 30]. Grades such as **48SH**, **45UH**, or **42EH** are likely choices, offering both a powerful magnetic field and superior thermal stability with operating temperatures from 150°C to 200°C [29]. This thermal resilience is non-negotiable for ensuring the motor's long-term performance and reliability in the demanding automotive environment.

The cost of medium stepper motors is substantially higher than that of small steppers, driven directly by the larger quantity and higher quality of the materials used. The primary cost drivers are the larger mass of copper, the larger stack of high-grade electrical steel, and most significantly, the larger and higher-grade NdFeB permanent magnet [74]. The cost of the magnet increases exponentially with both size and thermal grade, making it the dominant component of the material cost [29]. The inclusion of a high-precision planetary gearbox adds another significant layer of cost, as the manufacturing of machined alloy steel gears is an expensive process [71]. The supply chain for these specialized motors is managed by global firms with expertise in precision mechatronics, such as Nidec, Johnson Electric, and AMETEK [89, 92]. This supply chain is critically dependent on the availability of high-grade NdFeB magnets, amplifying the industry's exposure to the risks associated with the China-dominated rare earth market [81]. The procurement of these powerful magnets is a key strategic challenge, and any volatility in the rare earth market has a direct and significant impact on the production cost and stability of these essential BEV components.

## Part 4: Material Composition and Weight Analysis of Integrated Assemblies

The integration of gearboxes with auxiliary motors creates a complete mechatronic assembly whose material composition and weight are critical factors in vehicle design. This section analyzes the combined material breakdown of motor-gearbox units and examines the overall weight specifications and optimization strategies.

### Gearbox Integration and Material Composition

The choice of materials for gearbox components is a critical engineering decision that directly impacts performance, durability, weight, noise, and cost. In automotive auxiliary systems, a careful balance is struck between the high strength of traditional metals and the versatile properties of modern engineering plastics. The selection depends heavily on the specific application's load, speed, and environmental conditions. For components subjected to high stress, such as in power seat gearboxes, gears are typically manufactured from case-hardened steels, such as 20MnCr5, or other alloy steels. In many modern auxiliary motor gearboxes, where loads are lower and other factors like weight and noise are more critical, engineering plastics have become increasingly prevalent. Two of the most common plastics used for gears are Polyoxymethylene (POM) and Polyamide 66 (PA66), often reinforced with glass fibers (GF) or aramid fibers and blended with internal lubricants like PTFE to enhance strength and reduce wear.

The following tables provide an estimated material breakdown for the complete motor and gearbox assemblies.

#### TABLE 3: Estimated Material Composition - Small Stepper Motor + Gearbox Assembly

| Component Group | Material | Percentage of Total Assembly Weight |
| :--- | :--- | :--- |
| **Motor Components** | | **70% - 80%** |
| | Copper (Windings) | 15% - 25% |
| | Electrical Steel (Stator) | 30% - 40% |
| | NdFeB Magnet (Rotor) | 5% - 10% |
| | Housing/Structure (Plastic/Al) | 10% - 15% |
| **Gearbox Components** | | **20% - 30%** |
| | Gears (Plastic - POM/PA66) | 10% - 15% |
| | Housing (Plastic) | 5% - 10% |
| | Lubricants/Misc. | <5% |
| **Total Assembly** | | **100%** |

#### TABLE 4: Estimated Material Composition - Medium DC Motor + Gearbox Assembly

| Component Group | Material | Percentage (Metal Gearbox Variant) | Percentage (Plastic Gearbox Variant) |
| :--- | :--- | :--- | :--- |
| **Motor Components** | | **50% - 60%** | **65% - 75%** |
| | Copper (Windings) | 10% - 15% | 10% - 15% |
| | Electrical Steel (Stator/Rotor) | 20% - 25% | 25% - 30% |
| | Magnets (Ferrite/NdFeB) | 5% - 10% | 5% - 10% |
| | Housing/Structure (Al/Steel) | 10% - 15% | 15% - 20% |
| **Gearbox Components** | | **40% - 50%** | **25% - 35%** |
| | Gears (Alloy Steel) | 25% - 30% | - |
| | Gears (Plastic - POM/PA66+GF) | - | 15% - 20% |
| | Housing (Al/Steel) | 10% - 15% | - |
| | Housing (Plastic) | - | 5% - 10% |
| | Lubricants/Misc. | <5% | <5% |
| **Total Assembly** | | **100%** | **100%** |

#### TABLE 5: Estimated Material Composition - Medium Stepper Motor + Gearbox Assembly

| Component Group | Material | Percentage of Total Assembly Weight |
| :--- | :--- | :--- |
| **Motor Components** | | **60% - 70%** |
| | Copper (Windings) | 15% - 20% |
| | Electrical Steel (Stator) | 25% - 35% |
| | NdFeB Magnet (Rotor) | 10% - 15% |
| | Housing/Structure (Al/Steel) | 10% - 15% |
| **Gearbox Components** | | **30% - 40%** |
| | Gears (Alloy Steel/Powder Metallurgy) | 20% - 25% |
| | Housing (Al/Steel) | 5% - 10% |
| | Lubricants/Misc. | <5% |
| **Total Assembly** | | **100%** |

### Weight Analysis and Optimization

In the pursuit of maximizing the range and overall efficiency of BEVs, "lightweighting" has become a paramount design objective. This focus on mass reduction extends to all components, including auxiliary motor-gearbox assemblies. The integration of an appropriate gearbox allows for the use of smaller, lighter motors, contributing significantly to overall vehicle weight savings. Further optimization involves a multi-faceted approach, combining advanced design techniques, strategic material selection, and manufacturing process optimization.

A primary method for reducing weight is through targeted material removal using Finite Element Analysis (FEA). Engineers can create digital models to simulate operational stresses, revealing low-stress areas where material can be safely removed without compromising strength. This can result in material savings of around 2% per gear, which, while seemingly minor, has a substantial cumulative effect. More advanced is topology optimization, an algorithmic approach that determines the most efficient distribution of material. When applied to a gearbox housing, this can reduce weight by over 8% while simultaneously decreasing stress and deformation.

Material selection is another critical lever. The shift from steel and cast iron to lightweight alternatives like aluminum alloys for housings and engineering plastics (POM, PA66) for gears in low-to-moderate load applications provides significant weight savings. The design of the gearbox itself also plays a crucial role. Planetary gear systems are favored for their high power-to-weight and torque-to-weight ratios, transmitting high torque within a compact and lightweight package compared to traditional spur gear systems.

#### TABLE 6: Weight Ranges and Specifications for Motor-Gearbox Assemblies

| Motor Type | Motor Alone Weight (kg) | Gearbox Weight (kg) | Total Assembly Weight (kg) | Gearbox Weight as % of Total |
| :--- | :--- | :--- | :--- | :--- |
| **Small Stepper Motor** | 0.15 - 0.30 | 0.05 - 0.10 | **0.2 - 0.4** | 20% - 30% |
| **Medium DC Motor (Plastic Gearbox)** | 0.4 - 0.8 | 0.2 - 0.4 | **0.6 - 1.2** | 25% - 35% |
| **Medium DC Motor (Metal Gearbox)** | 0.5 - 1.5 | 0.5 - 1.5 | **1.0 - 3.0** | 40% - 50% |
| **Medium Stepper Motor** | 0.5 - 1.0 | 0.2 - 0.5 | **0.7 - 1.5** | 30% - 40% |

## Part 5: Gearbox Specifications and Application

The selection of a gearbox for an automotive auxiliary application is a critical design choice that influences performance, durability, noise, and packaging. The three most common types of gearboxes used in these systems are planetary, worm, and spur gearboxes. Each has a distinct set of characteristics that makes it suitable for specific functions within the vehicle.

**Planetary Gearboxes**, also known as epicyclic gear trains, are renowned for their high torque density and compact size. Their unique construction, with a central sun gear, multiple planet gears, and an outer ring gear, allows them to distribute load across multiple gear teeth simultaneously. This enables them to handle significantly higher torque than a spur gearbox of a similar size. This high torque capacity, combined with their concentric input and output shafts, makes them exceptionally compact and ideal for applications where space is at a premium, such as power seat adjustment mechanisms and high-force headlamp actuators.

**Worm Gearboxes** are composed of a screw-like worm and a worm wheel. Their most notable characteristic is the capacity for very high gear reduction ratios in a single stage, often ranging from 20:1 to over 300:1. This makes them extremely effective at converting high-speed motor rotation into very low-speed, high-torque output. Another key feature is their self-locking or non-reversible nature. Due to high friction, the worm wheel cannot drive the worm, acting as a natural brake. This property is highly desirable in applications like power window regulators, as it prevents the window from being manually forced down, adding security without an additional braking mechanism.

**Spur Gearboxes** are the simplest and most common type, consisting of one or more pairs of straight-toothed gears on parallel shafts. Their main advantages are simplicity and low manufacturing cost. They are straightforward to design and produce, making them a cost-effective solution for many applications. However, the engagement of the straight-cut teeth can generate considerable noise, making them less suitable for applications where quiet operation is a priority. In automotive auxiliary systems, spur gears are typically found in lower-torque, lower-precision applications where cost is a primary driver, such as in some HVAC actuators.

### TABLE 7: Gearbox Specifications by Motor Type

| Motor Type | Gearbox Prevalence (%) | Common Gearbox Types | Typical Gear Ratios | Gearbox Weight Range (kg) | Gearbox Material (Metal/Plastic) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Small Stepper Motor** | >95% | Spur, Planetary | 20:1 - 150:1 | 0.05 - 0.10 | Plastic |
| **Medium DC Motor** | ~90% | Worm, Planetary | 20:1 - 2000:1 | 0.2 - 1.5 | Metal and/or Plastic |
| **Medium Stepper Motor** | >95% | Planetary, Worm | 50:1 - 200:1 | 0.2 - 0.5 | Metal |

### TABLE 8: Gear Ratios by Application

| Application | Motor Type | Gearbox Type | Gear Ratio Range | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Seat Slide/Recline** | Medium DC | Planetary | 20:1 - 100:1+ | High torque for moving occupant weight; compact size for integration. |
| **Window Regulator** | Medium DC | Worm | 50:1 - 2000:1 | Very high torque for lifting glass; self-locking for security and holding position. |
| **Power Mirror Adjust** | Medium DC | Spur/Planetary | ~120:1 | High ratio provides fine control and slow, precise movement; low torque required. |
| **HVAC Actuator** | Small Stepper | Spur/Planetary | 20:1 - 150:1 | Provides necessary torque to move flaps against air pressure; enables precise positioning. |
| **Headlamp Leveling** | Medium Stepper | Planetary | 50:1 - 200:1 | High torque for fast, precise, and forceful movement of the entire lamp assembly. |
| **Active Grille Shutter** | Medium Stepper | Planetary/Worm | 50:1 - 200:1 | High torque to operate against air pressure at speed; holds position securely. |
| **Power Liftgate** | Medium DC | Worm/Planetary | 50:1 - 150:1 | High torque to lift and hold heavy liftgate; controlled speed for safety. |

## Synthesis and Conclusion

This comprehensive and updated analysis of auxiliary electric motors in 2024-2026 model year BEVs confirms their foundational role in the modern vehicle and reveals a sophisticated, multi-tiered ecosystem of electromechanical components. The investigation confirms the distinct and critical roles of small stepper motors, medium DC motors, and, crucially, medium stepper motors, each selected based on a careful engineering balance of precision, power, efficiency, and cost. A central conclusion of this report is that the functionality of these motors is inseparable from their integrated gearboxes. The use of planetary, worm, and spur gear systems is not an exception but the rule for nearly all actuation tasks, enabling the use of smaller, lighter, and more efficient motors by providing essential torque multiplication and speed reduction.

Small stepper motors, with power ratings under 50 watts, remain the component of choice for low-force, high-precision applications, most notably in the vast majority of HVAC system actuators [105, 106]. When paired with simple plastic spur or planetary gearboxes, they provide the accurate, repeatable control necessary for fine-tuning the cabin environment.

Medium DC motors, particularly brushless variants in the 50 to 500-watt range, are the undisputed workhorses for continuous-duty and high-force applications. Their role in driving direct-drive electric water pumps for thermal management is fundamental to BEV performance [123, 124]. For all other high-force tasks, they are paired with robust gearboxes: worm gears for the self-locking security needed in window lifts, and high-torque planetary gears for the immense force required by power seats.

This report's updated framework correctly identifies the significant and growing role of medium stepper motors (50-200W). Paired with high-ratio planetary or worm gearboxes, this category is a critical enabler of advanced features requiring both precision and force, such as adaptive headlamps, active grille shutters, and charging port locks [109, 113, 118].

Across all motor types that prioritize performance and compact size, a clear trend emerges: a deep reliance on advanced materials, particularly high-grade non-grain oriented electrical steel and, most importantly, high-strength Neodymium Iron Boron (NdFeB) permanent magnets [22, 29, 30]. This reliance, however, exposes the industry to significant challenges. The costs of two key materials—**copper** and **rare earth elements**—are major drivers of volatility [74, 97]. The price of copper, essential for all motor windings, is subject to sustained upward pressure from global electrification [99, 100]. More critically, the cost and availability of NdFeB magnets, which can dominate the material cost of a high-performance motor, are subject to the extreme price volatility and geopolitical risks inherent in the rare earth market [74, 81].

This leads to the report's most critical conclusion regarding the supply chain: the automotive industry's profound and systemic dependence on China for the processing of rare earth elements and the production of permanent magnets constitutes a strategic vulnerability of the highest order [81]. This single-point-of-failure risk threatens the stability and cost structure of BEV production worldwide. In response, a necessary and urgent strategic shift is underway. Automakers, suppliers, and governments are now actively collaborating to de-risk this critical supply chain through a multi-pronged approach that includes the diversification of sourcing, direct investment in non-Chinese mining and processing infrastructure, and long-term research into alternative magnet materials and rare-earth-free motor designs [81, 82, 84]. The future design, cost, and uninterrupted production of the hundreds of millions of auxiliary motor-gearbox assemblies required for the transition to electric mobility will be inextricably linked to the successful navigation of these complex material and supply chain challenges.

# References
1. [what are the three types of stepper motors? - Smooth Motor](https://www.smoothmotor.com/blog/what-are-the-three-types-of-stepper-motors.html)
2. [Stepper motor - Wikipedia](https://en.wikipedia.org/wiki/Stepper_motor)
3. [Stepper Motors: Part 1 – An Overview - EE Power](https://eepower.com/technical-articles/stepper-motors-part-1-an-overview/)
4. [Stepper Motors: typologies and technical features - Electric Motor Engineering](https://www.electricmotorengineering.com/stepper-motors-typologies-and-technical-features/)
5. [Stepper Motor Selection Guide - Motion Control Products](https://motioncontrolproducts.com/resources/stepper-motor-selection-guide)
6. [Applications of Stepper Motors in the Automotive Industry - Smooth Motor](https://www.smoothmotor.com/applications-of-stepper-motors-in-the-automotive-industry-blog)
7. [NEMA 17 Stepper motor - RepRap](https://reprap.org/wiki/NEMA_17_Stepper_motor)
8. [Nema 17 Stepper Motor - ATO](https://www.ato.com/Content/doc/nema-17-stepper-motor-specs.pdf)
9. [Stepper Motor Specifications, NEMA 17 1.8 Degree 200 Steps-per-revolution Four-phase Unipolar Permanent-magnet Stepper-motor - Mosaic Industries](http://www.mosaic-industries.com/embedded-systems/microcontroller-projects/stepper-motors/specifications)
10. [Nema-17 1.5A High Torque 80N.cm Stepper Motor - Handson Technology](https://www.handsontec.com/dataspecs/motor_fan/nema17-42BYGH60.pdf)
11. [NEMA17-06 - Joy-IT](https://joy-it.net/en/products/NEMA17-06)
12. [Nema 17 - 42 x 42mm Stepper Motor - STEPPERONLINE](https://www.omc-stepperonline.com/nema-17-stepper-motor)
13. [Ultimate Guide to Recycling Electric Motors - Recycle Your Metal](https://recycleyourmetal.com/ultimate-guide-to-recycling-electric-motors/)
14. [How Much Copper Wire Is In Industrial Motors? - A Plus Electric Motor Repair](https://apluselectricmotor.repair/copper-wire-is-in-industrial-motors/)
15. [Scrap Electric Motors - Okon Recycling](https://www.okonrecycling.com/industrial-scrap-metal-recycling/copper-recovery/scrap-electric-motors/)
16. [Copper (Fractional Electric Motor Scrap) - Scrap Monster](https://www.scrapmonster.com/scrap/copper-fractional-electric-motor-scrap/17)
17. [How much copper is there per kw for motor or generator? Is there a chart for reference? - Quora](https://www.quora.com/How-much-copper-is-there-per-kw-for-motor-or-generator-Is-there-a-chart-for-reference)
18. [Types of Scrap Electric Motors & How To Scrap Them - iScrap App](https://iscrapapp.com/blog/types-of-scrap-electric-motors-how-to-scrap-them/)
19. [Copper to iron ratio in transformers and electric motors - Scrap Metal Forum](https://www.scrapmetalforum.com/general-electronics-recycling/9677-copper-iron-ratio-transformers-electric-motors.html)
20. [How much copper is in an electric motor - Metallobaza](https://metall.biz.ua/en/index.php?route=extension/blog/blog&blog_id=152)
21. [Steel for rotors & stators - Waelzholz](https://www.waelzholz.com/en/sustainability/technologies/future-steel-materials/steel-for-rotors-stators.html)
22. [How Electrical Steel Grade Selection Drives Efficiency in Stator Core Laminations - Gator Lamination](https://www.gatorlamination.com/how-electrical-steel-grade-selection-drives-efficiency-in-stator-core-laminations/)
23. [Electrical steel - Wikipedia](https://en.wikipedia.org/wiki/Electrical_steel)
24. [Electric Motor Stator: The Ultimate Guide - YUCCA](https://yucca-motorlamination.com/electric-motor-stator/)
25. [How to Select the Right Grade of Silicon Steel for Your Motor? - LAM](https://lammotor.com/select-right-grade-of-silicon-steel/)
26. [Electrical Steel Grades - LAM365](https://lam365.com/electrical-steel-grades/)
27. [Stator Cores - an overview | ScienceDirect Topics - ScienceDirect](https://www.sciencedirect.com/topics/engineering/stator-cores)
28. [Application of Ndfeb neodymium magnet in stepper motor - Courage Magnet](https://www.couragemagnet.com/magnet-blog/949.html)
29. [NdFeB Magnet Grade Selection for Motors: How to Match the Right Grade to Maximize Performance and Reliability? - Mainrich Magnets](https://mainrichmagnets.com/ndfeb-magnet-grade-selection-for-motors)
30. [Motor Applications of NdFeB Magnets - Quadrant](https://www.quadrant.us/blog/1537.html)
31. [What is NdFeB Magnet? A Complete Guide to Neodymium Magnets - Tongchuang](https://www.ndmagnets.com/what-is-ndfeb-magnet-a-complete-guide-to-neodymium-magnets/)
32. [Application of Neodymium Magnets in Motors - Stanford Magnets](https://www.stanfordmagnets.com/application-of-neodymium-magnets-in-motors.html)
33. [Unlocking Power: How Neodymium Magnets Revolutionize Motor Performance? - Mainrich Magnets](https://mainrichmagnets.com/how-neodymium-magnets-improve-motor-performance)
34. [What Motors can be Used for NdFeB Magnets? - Stanford Magnets](https://www.stanfordmagnets.com/what-motors-can-be-used-for-ndfeb-magnets.html)
35. [DC motor 500w - Servovision](https://www.servovision.com/DC%20Motor%20%20%20PMDC%20Motor%20PermanentMagnet%20DC%20Motor/DC%20motor%20500w.html)
36. [Diydeg Brushed Electric, 24V 500W Brushed Speed Reduction Motor 2800RPM Reduction Electric Motor for Electric Scooter E Bike Go Kart - Amazon](https://www.amazon.com/Diydeg-Brushed-Electric-2800RPM-Reduction/dp/B0B69BJB5N)
37. [1600rpm 500w 90v brushed dc motor - Volcano Motor](http://www.volcanomotor.com/products/1600rpm_500w_90v_brushed_dc_motor-en.html)
38. [24V 500W Brushless DC Motor - Brushless.com](https://www.brushless.com/24v-500w-brushless-dc-motor)
39. [DC Gearless 500 Watt Motor for E-bike - Matha Electronics](https://robosap.in/wp-content/uploads/2022/02/my1020-dc-gear-less-motor-for-ebike-electric-bicycle-250x250-1.jpg)
40. [500W Brushless DC Motor - DMK Motor](https://m.media-amazon.com/images/I/71oaVJOLJmL._AC_UF1000,1000_QL80_.jpg)
41. [Unite MY8216 200W 12V/24V DC Motor - High-Speed Performance at 3200 RPM - Motion Dynamics](https://www.motiondynamics.com.au/unite-my8216-200w-12v-or-24v-dc-motor-3200-rpm.html)
42. [12V 200W 0.64 Nm 3000 rpm 20.8A Brushless DC Motor - Lunyee](https://www.lunyee.com/products/12v-200w-0.64-nm-3000-rpm-20.8a-brushless-dc-motor.html)
43. [200W Brushless DC Motor, 12V/24V/48V, 3000rpm - Peaco Support](https://peacosupport.com/200w-brushless-dc-motor)
44. [Get 200W M077A-4435 12-volt Brushless DC Motor From Emppl - Emppl](https://www.emppl.com/products/m077a-4435)
45. [12V 200W Brushless DC Motor, 0.64 Nm, 3000 rpm, 20.8A - Brushless.com](https://www.brushless.com/12v-200w-brushless-dc-motor)
46. [Are copper or aluminium windings better for electric motors? - Fisher & Paykel Technologies](https://www.fisherpaykeltechnologies.com/knowledge-hub/are-copper-or-aluminium-windings-better-for-electric-motors)
47. [How to Identify Motors with Aluminum vs. Copper Windings - German-Gulf Enterprises Ltd.](https://www.germanatj.com/blog/how-to-identify-motors-with-aluminum-vs.-copper-windings.html)
48. [Copper Winding Vs Aluminum Winding in the Motor - Aarohi Embedded Systems](https://www.aarohies.com/copper-winding-vs-aluminum-winding-in-the-motor/)
49. [The Differences Between Pure Copper Winding Motors and Aluminum Winding Motors - DFV FAN](https://www.dfvfan.com/article/the-differences-between-pure-copper-winding-motors-and-aluminum-winding-motors.html)
50. [Advantages Of Using Pure Copper Coils For Motors - VSDMOTOR](https://www.vsdmotor.com/info/advantages-of-using-pure-copper-coils-for-moto-73709620.html)
51. [Copper vs. Aluminum Windings in Motors - ACHR News](https://www.achrnews.com/articles/83673-copper-vs-aluminum-windings-in-motors)
52. [Copper Motor VS Aluminum Motor - BSGH Equipment](https://bsghgranulator.com/copper-motor-vs-aluminum-motor/)
53. [What is the housing material of electric motors? - EMP Casing](https://empcasting.com/what-is-the-housing-material-of-electric-motors.html)
54. [From Forge to Factory: How Motors Are Made - PDF Electric & Supply Company](https://www.pdfsupply.com/blog/index.php/2023/06/12/from-forge-to-factory-how-motors-are-made/)
55. [Demystifying the Materials Used in Motor Housings - KT Foundry](https://kt-foundry.com/demystifying-the-materials-used-in-motor-housings/)
56. [e-motor materials - E-Mobility Engineering](https://www.emobility-engineering.com/emotor-materials/)
57. [Motor shaft material - Mechanical engineering general discussion - Eng-Tips](https://www.eng-tips.com/threads/motor-shaft-material.461308/)
58. [Choosing the Right Material for Shafts - Sinotech](https://sinotech.com/blog/choosing-material-for-shafts/)
59. [Motor casing material discussion - DIY Electric Car](https://www.diyelectriccar.com/threads/motor-casing-material-discussion.72202/)
60. [Neodymium vs Ferrite Magnets - Ideal Magnet Solutions](https://idealmagnetsolutions.com/knowledge-base/neodymium-vs-ferrite-magnets/)
61. [Neodymium Magnets vs Ferrite Magnets - Stanford Magnets](https://www.stanfordmagnets.com/neodymium-magnets-vs-ferrite-magnets.html)
62. [Ferrite & Neodymium Magnets in Industrial Applications - Okon Recycling](https://www.okonrecycling.com/magnet-recycling-and-applications/magnet-technology/ferrite-neodymium-magnets-industrial-applications/)
63. [Magnets for Motor Applications - Adams Magnetic Products](https://www.adamsmagnetic.com/applications-and-markets-served/magnets-motor-applications/)
64. [Neodymium Magnet vs Ferrite Magnet: Know the Differences - Rochester Magnet](https://rochestermagnet.com/blog/entry/neodymium-magnet-vs-ferrite-magnet-know-the-differences/)
65. [What is the difference between rare earth and ferrite magnets? - Fisher & Paykel Technologies](https://www.fisherpaykeltechnologies.com/knowledge-hub/what-is-the-difference-between-rare-earth-and-ferrite-magnets)
66. [Difference Between Neodymium Magnets and Ferrite Magnets - Stanford Magnets](https://www.stanfordmagnets.com/difference-between-neodymium-magnets-and-ferrite-magnets.html)
67. [Motor Magnets - SuperMagnetMan](https://supermagnetman.com/collections/motor-magnets)
68. [Nema 23 Stepper Motor - ATO](https://www.ato.com/Content/doc/nema-23-stepper-motor-specs.pdf)
69. [NEMA 23 Stepper Motor Datasheet, Specs - Components101](https://components101.com/motors/nema-23-stepper-motor-datasheet-specs)
70. [Nema 23 Stepper Motor L:76mm Gear Ratio 50:1 MG Series Planetary Gearbox - STEPPERONLINE](https://www.omc-stepperonline.com/nema-23-stepper-motor-l-76mm-gear-ratio-50-1-mg-series-planetary-gearbox-23hs30-2904s-mg50)
71. [Nema 23 Stepper Motor L:55mm Gear Ratio 50:1 High Precision Planetary Gearbox - STEPPERONLINE](https://www.omc-stepperonline.com/nema-23-stepper-motor-l-55mm-gear-ratio-50-1-high-precision-planetary-gearbox-23hs22-2804s-hg50)
72. [Stepper Motor - NEMA 23 (High Torque 269oz-in) (X-50 & X-Rails, PRO Series Y-Rails) - Onefinity CNC](https://static.wixstatic.com/media/f704eb_db680f04d2fe4aef9b5a9314163fcfde~mv2.png/v1/fill/w_252,h_252,q_90,enc_avif,quality_auto/f704eb_db680f04d2fe4aef9b5a9314163fcfde~mv2.png)
73. [Stepper Motor: NEMA-23, 125 oz.in, 200 steps/rev - pishop.us](https://www.pishop.us/product/stepper-motor-nema-23-125-oz-in-200-stepsrev/)
74. [Cost and Performance of EV-Specific Components - ANL](https://publications.anl.gov/anlpubs/2000/05/36138.pdf)
75. [A cost model for permanent magnet synchronous machines - SpringerLink](https://link.springer.com/article/10.1007/s41104-023-00128-w)
76. [How Much Do Electric Motors Really Cost? - Pumps & Systems](https://www.pumpsandsystems.com/how-much-do-electric-motors-really-cost)
77. [On the Road to Full-Scale Production of Electric Vehicles: An Analysis of the Automakers' Costs and the Government's Role - eScholarship](https://escholarship.org/content/qt0vn7x67p/qt0vn7x67p_noSplash_441baf018c30a832aa16138a6c353b95.pdf)
78. [Electric vehicle raw material costs have more than doubled during the pandemic - CNBC](https://www.cnbc.com/2022/06/22/electric-vehicle-raw-material-costs-doubled-during-pandemic.html)
79. [An Overview of Costs for Vehicle Components, Fuels, Greenhouse Gas Emissions and Total Cost of Ownership (Update 2017) - UC Davis](https://steps.ucdavis.edu/wp-content/uploads/2018/02/FRIES-MICHAEL-An-Overview-of-Costs-for-Vehicle-Components-Fuels-Greenhouse-Gas-Emissions-and-Total-Cost-of-Ownership-Update-2017-.pdf)
80. [MarkLines Co., Ltd. - MarkLines](https://www.marklines.com/en/teardown/drive_motor)
81. [The Automotive Industry's Rare Earth Reliance: From Metals to Magnets in a Geopolitically Fragile Era - Rare Earth Exchanges](https://rareearthexchanges.com/news/the-automotive-industrys-rare-earth-reliance-from-metals-to-magnets-in-a-geopolitically-fragile-era/)
82. [USA Rare Earth](https://www.usare.com/)
83. [About - USA Rare Earth](https://www.usare.com/about)
84. [U.S. Mined and Processed Rare Earths Successfully Manufactured into Permanent Magnets for Use in EVs and Hybrids - PR Newswire](https://www.prnewswire.com/news-releases/us-mined-and-processed-rare-earths-successfully-manufactured-into-permanent-magnets-for-use-in-evs-and-hybrids-302548989.html)
85. [USA Rare Earth Closes Acquisition of Less Common Metals - USA Rare Earth](https://www.usare.com/article?i=159729)
86. [Capabilities - USA Rare Earth](https://www.usare.com/capabilities)
87. [Ex-China rare earths magnet producers move to secure supplies of raw materials - Fastmarkets](https://www.fastmarkets.com/insights/rare-earths-supply-chain/)
88. [Automotive Auxiliary Motors Research Reports & Market Industry Analysis - Mordor Intelligence](https://www.mordorintelligence.com/market-analysis/automotive-auxiliary-motors)
89. [Top 10 Electric Motor Manufacturers in the World (2025 Guide) – How to Choose the Right Supplier - RUITO Motor](https://ruitomotor.com/top-10-electric-motor-manufacturers-in-the-world/)
90. [Top 7 Automotive Motor Companies| Verified Market Research - Verified Market Research](https://www.verifiedmarketresearch.com/blog/top-automotive-motor-companies/)
91. [Automotive Auxiliary Motors and Sensors Market: A Comprehensive Analysis - Market Business Insights - Market Business Insights](https://www.marketbusinessinsights.com/automotive-auxiliary-motors-and-sensors-market)
92. [6 Automotive Motor Manufacturers in 2025 | Metoree - Metoree](https://us.metoree.com/categories/7851/)
93. [Automotive auxiliary systems | Infineon Technologies - Infineon Technologies](https://www.infineon.com/applications/automotive/body-electronics-power-distribution/auxiliary-systems)
94. [YASA Limited | Axial Flux Motors For Electric Vehicles | YASA - YASA Limited](https://yasa.com/)
95. [Top 10 Electric Motor Manufacturers in the World 2025 - Twirl Motor - Twirl Motor](https://www.twirlmotor.com/top-electric-motor-manufacturers-in-the-world/)
96. [Copper Price Updates & Cost Index | January 2026 - Gordian](https://www.gordian.com/resources/copper-price-updates/)
97. [Electric Motor Market Size, Share, Growth | Report, 2032 - Fortune Business Insights](https://www.fortunebusinessinsights.com/industry-reports/electric-motor-market-100752)
98. [Copper Price: What influences the price, risks and opportunities - Banco Carregosa](https://www.bancocarregosa.com/en/insights/conteudos/copper-price-what-influences-the-price-risks-and-opportunities/)
99. [Copper: Major Factors That Offer Two Opposing Price Scenarios - CME Group](https://www.cmegroup.com/insights/economic-research/2025/copper-major-factors-that-offer-two-opposing-price-scenarios.html)
100. [Why Copper Prices Are Surging and What to Expect - Carbon Credits](https://carboncredits.com/why-copper-prices-are-surging-and-what-to-expect/)
101. [Copper prices in 2024 and 2025: a global overview and analysis - Fastmarkets](https://www.fastmarkets.com/insights/copper-prices-in-2024-and-2025-a-global-overview-and-analysis/)
102. [E-Mobility Factsheet - International Copper Association](https://internationalcopper.org/wp-content/uploads/2017/06/2017.06-E-Mobility-Factsheet-1.pdf)
103. [HVAC Heater Blend Door Actuator - Duallane Truck Parts](https://www.duallane.com/shop-parts/hvac/hvac-blowers-controls/hvac-heater-blend-door-actuator)
104. [000906920864 - Stepper Motor 2019-2025 Mercedes-Benz - Mercedes-Benz USA](https://mbparts.mbusa.com/oem-parts/mercedes-benz-hvac-blend-door-actuator-9069208)
105. [(PDF) STEPPER MOTOR ACTUATOR FOR HVAC BLEND DOOR -A REVIEW - Academia.edu](https://www.academia.edu/40175828/STEPPER_MOTOR_ACTUATOR_FOR_HVAC_BLEND_DOOR_A_REVIEW)
106. [Stepper Stepper Motor Motor Actuator Actuator for for HVAC Blend Door HVAC Blend Door – A Review by Transtellar Publications - Issuu - Transtellar Publications](https://i.ytimg.com/vi/3Vjt76jzzcE/maxresdefault.jpg)
107. [13192013 by OES | Blend Door Actuator (Stepper Motor) - eSaabParts](https://farm1.staticflickr.com/819/40121813855_c177e92b6c_k.jpg)
108. [Headlamp Levelling Systems - HELLA](https://www.hella.com/techworld/us/technical/automotive-lighting/headlamp-levelling-system/)
109. [Stepper motors assist adaptive headlights - EE Times](https://www.eetimes.com/stepper-motors-assist-adaptive-headlights/)
110. [headlamp leveling motors - Alibaba.com](https://www.alibaba.com/showroom/headlamp-leveling-motors.html)
111. [Automotive 2-Channel Stepper Motor Driver for Dynamic Headlight Reference Design - Texas Instruments](https://www.ti.com/tool/TIDA-020026)
112. [Stepper motors assist adaptive headlights - EDN](https://www.edn.com/stepper-motors-assist-adaptive-headlights/)
113. [Actuator-Motor,5877R1006 5877R1007 BLDC Stepper Shutter Actuator Motor Compatible with 2016-2021 Cherokee,2019-2021 1500,2021-2022 Escape - Amazon.com](https://ae01.alicdn.com/kf/S1981e68a0af94b139f56852a80617290B.jpg_960x960.jpg)
114. [Pleoos Idle Speed Control Valve, Replacement for King Kong Idle Motor 90380-10526 90325864 - Amazon.com](https://i.ebayimg.com/images/g/NXgAAOSwsrpne1CV/s-l1200.jpg)
115. [JawGrew Automotive Throttle Stepper Motor, Adjustable Idle Speed Control Valve, Compatible with King Kong Idle Motor - Amazon.com](https://i.pinimg.com/originals/17/e7/b9/17e7b9f7a3a5bfa2f24f4a7cc18a5f9b.jpg)
116. [gunroil Automotive Throttle Stepper Motor, Modified Accessories, Compatible with King Kong Idle Motor - Amazon.com](https://i.pinimg.com/originals/6a/85/cb/6a85cb44c062b80b17118b34b8136ace.jpg)
117. [90380-10526 90325864 Throttle Stepper Motor, Stable Operation - Amazon.com](https://i.ebayimg.com/images/g/iCAAAOSw6idne1D1/s-l400.jpg)
118. [Genuine OEM Drive Motor Battery Pack Charging Port Door Release Actuator For BMW - eBay](https://i.ebayimg.com/images/g/pawAAOSwoo5mfqW1/s-l1200.jpg)
119. [Control, central locking system - Smoothbev](https://smoothbev.com/products/control-central-locking-system/)
120. [Genuine OEM Drive Motor Battery Pack Charging Port Door Release Actuator For BMW I01 i3 i3s 2014-2020 - Amazon.com](https://wolfautoparts.com/media/catalog/product/9/f/9f83bf86440feb29df8cc18514c30777d23634736ad87ac8947fedc5438dbe87.jpeg?width=700&height=700&store=default&image-type=image)
121. [Charging Port Release Actuator - Smoothbev](https://smoothbev.com/products/charging-port-release-actuator-3)
122. [Actuator, charge port - Smoothbev](https://smoothbev.com/products/actuator-charge-port)
123. [Water Pump Energy Calculator: Watts and kWh - EnergyBot](https://www.energybot.com/energy-usage/water-pump.html)
124. [Calculating Water Pump Power Consumption - Explorist.life](https://explorist.life/water-pump-how-much-for-a-mobile-marine-or-off-grid-electrical-system/)
125. [Submersible pump power consumption - Solar-Electric.com Forum](https://forum.solar-electric.com/discussion/357504/submersible-pump-power-consumption)
126. [r/SolarDIY on Reddit: Calculating power usage of water pump - Reddit](https://www.reddit.com/r/SolarDIY/comments/pxb31p/calculating_power_usage_of_water_pump/)
127. [How Many Watts Does a Well Pump Use | Nature's Generator - Nature's Generator](https://naturesgenerator.com/blogs/news/how-many-watts-does-a-well-pump-use)