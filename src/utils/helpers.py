import numpy as np
import pandas as pd


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
    def add_cyclical_features(df, column_name, period, prefix=None):
        """
        Convert a numeric cyclical feature into sine and cosine components.
        :param df: DataFrame to update.
        :param column_name: Name of the original feature.
        :param period: Number of steps in one full cycle.
        :param prefix: Optional feature name prefix. If omitted, uses column_name.
        :return: DataFrame with added cyclical columns.
        """
        feature_prefix = prefix or column_name
        df[f"{feature_prefix}_sin"] = np.sin(2 * np.pi * df[column_name] / period)
        df[f"{feature_prefix}_cos"] = np.cos(2 * np.pi * df[column_name] / period)
        return df

    @staticmethod
    def convert_hour_to_cyclical(df, hour_column='hour'):
        """
        Convert hour column to cyclical features (sine and cosine).
        :param df: DataFrame containing the hour column.
        :param hour_column: Name of the hour column in the DataFrame.
        :return: DataFrame with added cyclical features.
        """
        return Helpers.add_cyclical_features(df, hour_column, 24, 'hour')

    @staticmethod
    def convert_month_to_cyclical(df, month_column='month'):
        """
        Convert month column to cyclical features (sine and cosine).
        :param df: DataFrame containing the month column.
        :param month_column: Name of the month column in the DataFrame.
        :return: DataFrame with added cyclical features.
        """
        return Helpers.add_cyclical_features(df, month_column, 12, 'month')

    @staticmethod
    def convert_day_of_week_to_cyclical(df, day_column='day_of_week_num'):
        """
        Convert day-of-week into cyclical features for Monday/Sunday continuity.
        :param df: DataFrame containing the weekday index.
        :param day_column: Name of the day-of-week numeric column.
        :return: DataFrame with added cyclical features.
        """
        return Helpers.add_cyclical_features(df, day_column, 7, 'day')

    @staticmethod
    def encode_holiday(df, holiday_column='holiday'):
        """
        Convert holiday text labels into a binary flag consistent with production usage.
        :param df: DataFrame containing the holiday field.
        :param holiday_column: Column name to encode.
        :return: DataFrame with binary holiday flag.
        """
        df[holiday_column] = df[holiday_column].apply(
            lambda value: 0 if str(value).strip().lower() in {"not holiday", "none", "nan", ""} else 1
        )
        return df

    @staticmethod
    def prepare_datetime_features(df, date_time_column='date_time'):
        """
        Standardize datetime-derived features used for the traffic model.
        :param df: DataFrame containing a datetime column.
        :param date_time_column: Name of datetime column.
        :return: DataFrame with extracted time features.
        """
        df = df.copy()
        df[date_time_column] = pd.to_datetime(df[date_time_column], errors='coerce')
        df = df.sort_values(date_time_column).reset_index(drop=True)
        df['year'] = df[date_time_column].dt.year
        df['day_of_week_num'] = df[date_time_column].dt.dayofweek
        df = Helpers.convert_day_of_week_to_cyclical(df, 'day_of_week_num')
        return df

    @staticmethod
    def build_preprocessor(numerical_features, categorical_features):
        """
        Build the shared preprocessing pipeline used by the production model.
        :param numerical_features: List of numeric columns.
        :param categorical_features: List of categorical columns.
        :return: fitted ColumnTransformer.
        """
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        return ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numerical_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
            ]
        )

    @staticmethod
    def save_model_artifact(model, artifact_path):
        """
        Save a model artifact using joblib.
        :param model: Any scikit-learn compatible model or pipeline.
        :param artifact_path: File path to save the model.
        """
        import joblib

        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, artifact_path)
        return artifact_path
