"""Core configuration and settings for PlantPulse backend."""
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "PLANTPULSE"
    PROJECT_DESCRIPTION: str = "Intelligent Industrial Energy Optimisation for Sustainable Manufacturing"
    PROJECT_STATUS: str = "PROPOSED CONCEPT · DESIGN STAGE · NO RESULTS CLAIMED YET"
    DATA_PROVENANCE_DEFAULT: str = "SIMULATED / DEMONSTRATION DATA"
    MODEL_VERSION: str = "1.0.0-prototype"
    CONFIG_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "sqlite:///./plantpulse.db"
    
    # Default Electrical Baseline (3-phase 415V, 50Hz)
    NOMINAL_VOLTAGE_V: float = 415.0
    NOMINAL_FREQUENCY_HZ: float = 50.0
    VOLTAGE_MIN_V: float = 373.5   # -10%
    VOLTAGE_MAX_V: float = 456.5   # +10%
    FREQUENCY_MIN_HZ: float = 47.5 # -5%
    FREQUENCY_MAX_HZ: float = 52.5 # +5%
    POWER_FACTOR_MIN: float = 0.80
    
    # Economics & Carbon References (Configured Reference, not official figures)
    DEFAULT_TARIFF_PER_KWH: float = 0.18
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KWH: float = 0.42  # Grid average demonstration factor
    DEFAULT_RESTART_ALLOWANCE_KWH: float = 0.0
    
    # Alerting & Debounce
    ALERT_DEBOUNCE_COUNT: int = 3
    ALERT_HYSTERESIS_SECONDS: int = 300
    
    # JWT / Security (Default development secret)
    SECRET_KEY: str = os.getenv("PLANTPULSE_SECRET_KEY", "plantpulse-insecure-dev-secret-key-3phase-415v")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

settings = Settings()
