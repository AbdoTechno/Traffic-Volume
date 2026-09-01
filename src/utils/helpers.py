import numpy as np

class Helpers:
    def __init__(self):
        pass

    @staticmethod
    def celsius_to_kelvin(value):
        """
        Convert temperature from Celsius to Kelvin.
        :param value: numeric temperature in Celsius.
        :return: temperature in Kelvin.
        """
        return value + 273.15

    @staticmethod
    def convert_hour_to_cyclical(df, hour_column='hour'):
        """
        Convert hour column to cyclical features (sine and cosine).
        :param df: DataFrame containing the hour column.
        :param hour_column: Name of the hour column in the DataFrame.
        :return: DataFrame with added cyclical features.
        """
        df['hour_sin'] = np.sin(2 * np.pi * df[hour_column] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df[hour_column] / 24)
        return df

    @staticmethod
    def convert_month_to_cyclical(df, month_column='month'):
        """
        Convert month column to cyclical features (sine and cosine).
        :param df: DataFrame containing the month column.
        :param month_column: Name of the month column in the DataFrame.
        :return: DataFrame with added cyclical features.
        """
        df['month_sin'] = np.sin(2 * np.pi * df[month_column] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df[month_column] / 12)
        return df
    