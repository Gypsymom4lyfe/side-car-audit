# Sovereign Sidecar Physical Stack

This document describes a proposed, non-invasive hardware stack for observing
equipment state independently of its software. It is a design outline, not
implemented firmware or a validated wiring guide.

## Bill of materials

| Function | Candidate component | Interface and purpose |
| --- | --- | --- |
| Controller | ESP32 or Raspberry Pi Pico W | Reads sensors, keeps a bounded local observation buffer, and coordinates receipt creation. Select the exact board before assigning pins or power requirements. |
| Operator tap | PN532 NFC reader and compatible operator card | I2C or SPI connection. Identifies an operator and can initiate a review of recent observations. Card authentication and writable secure storage depend on the selected card and must be verified. |
| Power/activity observation | Hall-effect sensor (for example SS49E or KY-003) or appropriately rated split-core current transformer | GPIO or ADC input, as required by the sensor. Observes magnetic-field changes or current activity near an external conductor or relay. |
| Status indication observation | LDR module or TCS34725 color sensor | ADC or I2C input, respectively. Reads light changes from an existing status indicator without connecting to the equipment's control bus. |
| Protected signing (recommended) | Secure element or hardware-backed key store | Holds a device signing key separate from the operator card. Needed to authenticate receipts; a hash chain alone does not prove who created a receipt. |

Use electrical isolation and appropriately rated sensors when observing
equipment power. Do not connect a microcontroller GPIO directly to mains or
other hazardous voltages. Sensor placement, isolation, and enclosure design
must be validated for the target equipment and deployment environment.

## Verification cycle

1. The controller samples optical and magnetic/current sensors continuously
   and buffers timestamped observations locally.
2. A card tap authenticates or identifies an operator and triggers a review
   of the buffered observations against locally configured baseline rules.
3. The device creates a receipt containing the verification result and
   relevant observation references, signs it with the device key, and appends
   it to its local audit chain.
4. If the selected card supports authenticated writable storage, the device
   may also write a receipt reference or compact proof to the card. The local
   audit log remains the record of the complete receipt.

## Integrity and scope

The current Python `receipt_logger.py` implementation stores JSONL receipts
chained with SHA-256. It does not sign receipts, enforce append-only storage,
authenticate NFC cards, read sensors, or write to card memory. Hardware
firmware and a protected signing-key integration are future work.

Sensor readings provide evidence of observable physical signals; they do not
by themselves prove that a machine completed a particular operation or that
its internal data was correct. Baselines, thresholds, sampling intervals, and
sensor placement must be calibrated for each deployment. The design should
retain only the observations needed for institutional accountability and
avoid collecting personal or public activity data.
