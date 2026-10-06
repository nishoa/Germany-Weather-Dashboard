import streamlit as st
import openmeteo_requests
import requests_cache
from matplotlib import pyplot as plt
from retry_requests import retry
import numpy as np


GERMANY_CITIES_COORDS = {
    "Berlin": (52.52, 13.41),
    "Hamburg": (53.55, 9.99),
    "Munich": (48.14, 11.58),
    "Cologne": (50.94, 6.96),
    "Frankfurt am Main": (50.11, 8.68),
    "Stuttgart": (48.78, 9.18),
    "Düsseldorf": (51.23, 6.77),
    "Leipzig": (51.34, 12.37),
    "Dortmund": (51.51, 7.47),
    "Essen": (51.46, 7.01),
    "Bremen": (53.08, 8.80),
    "Dresden": (51.05, 13.74),
    "Hanover": (52.38, 9.73),
    "Nuremberg": (49.45, 11.08),
    "Duisburg": (51.43, 6.76),
}



@st.cache_data
def get_weather_data(coords: tuple[float, float], forecast_days: int = 7) -> np.ndarray:
    """Fetches hourly temperature data from Open-Meteo API for given coordinates."""
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    lat, lon = coords
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "forecast_days": forecast_days,
    }
    responses = openmeteo.weather_api(url, params = params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

    return hourly_temperature_2m

def calculate_hourly_profile(temps: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generates a 24-hour diurnal temperature profile plot with min-max shading."""
    matrix = temps.reshape(-1, 24)
    avg_temp = matrix.mean(axis=0)
    return avg_temp, matrix.min(axis=0), matrix.max(axis=0)

def create_weather_plot(avg_temp: np.ndarray, min_temp: np.ndarray, max_temp: np.ndarray):
    """Draws plot based on parameters that user has selected"""
    fig, ax = plt.subplots()
    ax.set(xlabel = "Hours", ylabel = "Temperature (Celsius)")
    ax.set_xticks(np.arange(0, 24, 2))
    ax.plot(avg_temp, label = "Average Temperature")
    ax.fill_between(np.arange(24), min_temp, max_temp, alpha=0.4, label = "Min–Max Range")
    ax.legend()
    ax.grid()

    return fig

def main():
    st.title("Daily Temperature Profile")
    selected_city = st.selectbox('Select a city:', GERMANY_CITIES_COORDS.keys())
    selected_days = st.slider('Select a day range:', min_value=3, max_value=14, step=1)

    # Fetch and compute statistics
    raw_temps = get_weather_data(GERMANY_CITIES_COORDS[selected_city], selected_days)
    avg_t, min_t, max_t = calculate_hourly_profile(raw_temps)

    # Render visualization
    fig = create_weather_plot(avg_t, min_t, max_t)
    st.pyplot(fig)
    plt.close(fig)

    # Display KPI metrics
    col1, col2, col3 = st.columns(3)
    col1.metric('Absolute maximum:', f"{max_t.max():.2f} °C", f"{max_t.max()-avg_t.mean():.2f} °C")
    col2.metric('Absolute minimum:', f"{min_t.min():.2f} °C", f"{min_t.min()-avg_t.mean():.2f} °C")
    col3.metric('Overall average temperature:', f"{avg_t.mean():.2f} °C")

if __name__ == "__main__":
    main()
