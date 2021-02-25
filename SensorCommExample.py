from datetime import datetime

import matplotlib.pyplot as plt
from pandas import DataFrame
from serial.tools import list_ports

from SensorModbus import ModbusMaster, ModbusUnit
from TargetTemperatureFloat import TargetTemperatureFloat


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

                        if name == 'TemperatureTarget':
                            printed_reading = TargetTemperatureFloat.to_string(reading)
                        else:
                            printed_reading = str(reading)

                        # print data
                        print("{0},{1},{2}".format(i, name, printed_reading))

                        # Add data to database
                        data = data.append({'Unit': f'{com_port}-{unit.slave_id}', 'Index': i, 'VariableName': name,
                                            'VariableValue': reading}, ignore_index=True)

                used_time = datetime.now() - start_time
                print(f'Time used: {used_time}')

    first_unit = data['Unit'].unique()[0]
    first_unit_data = data[(data['Unit'] == first_unit) & (data['VariableName'] == 'TemperatureDet')]
    print(first_unit_data)

    plt.plot(first_unit_data['Index'], first_unit_data['VariableValue'])
    plt.title('Internal Temperature of The First Sensor')
    plt.xlabel('Readings')
    plt.ylabel('Internal Temperature (C)')
    plt.show()


if __name__ == '__main__':
    main()