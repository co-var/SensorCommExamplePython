from datetime import datetime
from struct import unpack, pack
from time import sleep

import matplotlib.pyplot as plt
import serial
from modbus_tk import defines as cst, modbus_rtu
from modbus_tk.exceptions import ModbusInvalidResponseError
from pandas import DataFrame
from serial.tools import list_ports


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
        serial_master = modbus_rtu.RtuMaster(
            serial.Serial(port=com_port, baudrate=9600, bytesize=8, parity='E', stopbits=1, xonxoff=0)
        )
        serial_master.set_timeout(0.04)  # ModbusInvalidResponseError "Response length is invalid 0" if <0.04
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


def main():
    com_ports = sorted([comport.device for comport in list_ports.comports()])
    print(f'Found com ports: {com_ports}')

    data = DataFrame(columns=['Index', 'Unit', 'VariableName', 'VariableValue'])
    for com_port in com_ports:
        print(f'Searching {com_port}')

        with ModbusMaster(com_port) as modbus_master:
            units = []
            search_slave_id_to = 16  # 247 max
            for slave_id in range(1, search_slave_id_to + 1):
                print(f'Searching {com_port} {slave_id}')
                try:
                    unit = ModbusUnit(modbus_master, slave_id)
                    assert (unit.read_variable('SlaveAddress') == slave_id)
                    units.append(unit)
                except TimeoutError as e:
                    pass

            print(f'Found Units on {units}')

            for unit in units:
                start_time = datetime.now()

                for i in range(100):
                    names = ['TemperatureDet', 'TemperatureTarget']
                    for name in names:
                        reading = unit.read_variable(name)

                        # print data
                        print("{0},{1},{2}".format(i, name, reading))

                        # Add data to database
                        data = data.append({'Unit': f'{com_port}-{unit.slave_id}', 'Index': i, 'VariableName': name,
                                            'VariableValue': reading}, ignore_index=True)

                used_time = datetime.now() - start_time
                print(f'Time used: {used_time}')

    first_unit = data['Unit'].unique()[0]
    first_unit_data = data[(data['Unit'] == first_unit) & (data['VariableName'] == 'TemperatureDet')]
    print(first_unit_data)
    plt.plot(first_unit_data['VariableValue'])
    plt.show()


if __name__ == '__main__':
    main()