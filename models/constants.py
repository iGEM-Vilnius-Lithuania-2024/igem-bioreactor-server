from models.MesurementType import MeasurementType


def get_measurement_attribute(measurement_type):
    attribute = {
        MeasurementType.TEMPERATURE: lambda m: m.temperature,
        MeasurementType.PH: lambda m: m.ph,
    }[measurement_type]
    return attribute


YLABEL_DICT = {
    MeasurementType.TEMPERATURE: 'Temperature [°C]',
    MeasurementType.PH: 'pH'
}

TITLE_DICT = {
    MeasurementType.TEMPERATURE: 'Temperature',
    MeasurementType.PH: 'PH'
}