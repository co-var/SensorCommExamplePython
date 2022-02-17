from struct import pack, unpack
from time import sleep

from modbus_tk import defines as cst, modbus_rtu
from modbus_tk.exceptions import ModbusInvalidResponseError
from serial import Serial


class ModbusMaster:
    def __init__(self, com_port):
        self.com_port = com_port
        self._serial_master = ModbusMaster._create_serial_master(com_port)

    def read_registers(self, slave_id, address, reg_count):
        try:
            ret = self._serial_master.execute(slave_id, cst.READ_HOLDING_REGISTERS, address, reg_count)
            sleep(0.02)  # ModbusInvalidResponseError "Response length is invalid 0" raised without this
        except ModbusInvalidResponseError as e:
            raise TimeoutError

        return ret

    def __enter__(self):
        self._serial_master.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._serial_master.close()

    @staticmethod
    def _create_serial_master(com_port):
        serial = Serial(port=com_port, baudrate=9600, bytesize=8, parity='E', stopbits=1, xonxoff=0)
        serial_master = modbus_rtu.RtuMaster(serial)
        serial_master.set_timeout(0.04)  # ModbusInvalidResponseError "Response length is invalid 0" if <0.04
        serial.write_timeout = 0.04
        return serial_master


class ModbusVariable:
    def __init__(self, address, typ, count):
        self.address = address
        self.typ = typ
        self.count = count


class ModbusUnit:
    def __init__(self, modbus_master, slave_id):
        self.variables = {
            'SlaveAddress': ModbusVariable(0X0800, 'UInt16', 1),
            'TemperatureTarget': ModbusVariable(0X0400, 'Single', 2),
            'TemperatureDet': ModbusVariable(0X0404, 'Single', 2),
        }
        self.pack_fmts = {'UInt16': 'H', 'Single': 'f'}
        self.lsb_low_reg = True
        self.modbus_master = modbus_master
        self.slave_id = slave_id

    def _get_pack_regs(self, registers):
        if self.lsb_low_reg:
            reg = registers
        else:
            reg = reversed(registers)
        return reg

    def _get_pack_bytes(self, pack_regs):
        byts = b''
        for pack_reg in pack_regs:
            byts += pack('H', pack_reg)
        return byts

    def read_variable_at(self, address, fmt, reg_count):
        slave_id = self.slave_id
        registers = list(self.modbus_master.read_registers(slave_id, address, reg_count))
        pack_regs = self._get_pack_regs(registers)
        pack_bytes = self._get_pack_bytes(pack_regs)
        variable = unpack(fmt, pack_bytes)[0]
        return variable

    def read_variable(self, name):
        address = self.variables[name].address
        fmt = self.pack_fmts[self.variables[name].typ]
        count = self.variables[name].count
        return self.read_variable_at(address, fmt, count)

    def __repr__(self):
        return f'{self.modbus_master.com_port}-{self.slave_id}'
