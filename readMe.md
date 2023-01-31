# 本项目为蓝牙安全检测项目

## 低功耗蓝牙漏洞poc
### Link Layer Length Overflow CVE-2019-16336 CVE-2019-17519 
`python poc/ble/link_layer_length_overflow.py COM7 A4:C1:38:D8:AD:A9`

### LLID Deadlock CVE-2019-17061 CVE-2019-17060
`python poc/ble/llid_dealock.py COM7 A4:C1:38:D8:AD:A9`

### Truncated L2CAP	CVE-2019-17517
`python poc/ble/DA14580_exploit_att_crash.py COM7 A4:C1:38:D8:AD:A9`

### Silent Length Overflow	CVE-2019-17518
`python poc/ble/DA14680_exploit_silent_overflow.py COM7 A4:C1:38:D8:AD:A9`

### Public Key Crash CVE-2019-17520
`python poc/ble/CC2640R2_public_key_crash.py COM7 A4:C1:38:D8:AD:A9`

### Invalid Connection Request	CVE-2019-19193
`python poc/ble/CC_connection_req_crash.py COM7 A4:C1:38:D8:AD:A9`

### Invalid L2CAP Fragment	CVE-2019-19195
`python poc/ble/Microchip_invalid_lcap_fragment.py COM7 A4:C1:38:D8:AD:A9`

### Sequential ATT Deadlock	CVE-2019-19192
`python poc/ble/sequential_att_deadlock.py COM7 A4:C1:38:D8:AD:A9`

### Key Size Overflow	CVE-2019-19196
`python poc/ble/Telink_key_size_overflow.py COM7 A4:C1:38:D8:AD:A9`

### Zero LTK Installation	CVE-2019-19194
`python poc/ble/Telink_zero_ltk_installation.py COM7 A4:C1:38:D8:AD:A9`

### DHCheck Skip  CVE-2020-13593
`python poc/ble/non_compliance_dhcheck_skip.py COM7 A4:C1:38:D8:AD:A9`

### ESP32 HCI Desync CVE-2020-13595
`python poc/ble/esp32_hci_desync.py COM7 A4:C1:38:D8:AD:A9`

### EZephyr Invalid Sequence  CVE-2020-10061
`python poc/ble/zephyr_invalid_sequence.py COM7 A4:C1:38:D8:AD:A9`

### Invalid Channel Map CVE-2020-10069 CVE-2020-13594
`python poc/ble/invalid_channel_map.py COM7 A4:C1:38:D8:AD:A9`

## update

2023/1/30:创建项目
2023/1/30：低功耗蓝牙漏洞poc 