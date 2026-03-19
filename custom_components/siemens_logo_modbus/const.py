"""Constants for the Siemens Logo Modbus integration."""

DOMAIN = "siemens_logo_modbus"

# ── Config keys ───────────────────────────────────────────────────────────────
CONF_MODBUS_HOST        = "host"
CONF_MODBUS_PORT        = "port"
CONF_REFRESH_INTERVAL   = "refresh_interval"
CONF_INPUT_COUNT        = "input_count"
CONF_OUTPUT_COUNT       = "output_count"
CONF_M_COUNT            = "m_count"
CONF_V_COUNT            = "v_count"
CONF_AI_COUNT           = "ai_count"
CONF_AQ_COUNT           = "aq_count"
CONF_VW_COUNT           = "vw_count"
CONF_AM_COUNT           = "am_count"

# Special features
CONF_ENABLE_NQ          = "enable_nq"    # AQ1→NQ1-8, AQ2→NQ9-16 virtual outputs
CONF_ENABLE_M_SELECTOR  = "enable_m_selector"  # M10-M14 decimal selector

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_HOST             = ""
DEFAULT_PORT             = 510
DEFAULT_REFRESH_INTERVAL = 2
DEFAULT_INPUT_COUNT      = 20
DEFAULT_OUTPUT_COUNT     = 16
DEFAULT_M_COUNT          = 16
DEFAULT_V_COUNT          = 0
DEFAULT_AI_COUNT         = 0
DEFAULT_AQ_COUNT         = 0
DEFAULT_VW_COUNT         = 0
DEFAULT_AM_COUNT         = 0
DEFAULT_ENABLE_NQ        = False
DEFAULT_ENABLE_M_SELECTOR = False

# ── Hard limits ───────────────────────────────────────────────────────────────
MIN_REFRESH_INTERVAL = 1
MAX_REFRESH_INTERVAL = 10
I_MAX_COUNT          = 24
Q_MAX_COUNT          = 20
M_MAX_COUNT          = 64
V_MAX_COUNT          = 6808
AI_MAX_COUNT         = 8
AQ_MAX_COUNT         = 8
VW_MAX_COUNT         = 425
AM_MAX_COUNT         = 64

# NQ virtual outputs: AQ1 bits → NQ1-8, AQ2 bits → NQ9-16
NQ_AQ1_MODBUS_ADDR   = 512   # AQ1 holding register (0-based)
NQ_AQ2_MODBUS_ADDR   = 513   # AQ2 holding register (0-based)
NQ_COUNT             = 16

# M10-M14 selector: 5 memory coils → decimal value 0-31
M_SELECTOR_START     = 9     # M10 = index 9 (0-based)
M_SELECTOR_COUNT     = 5     # M10..M14
M_SELECTOR_MIN       = 0
M_SELECTOR_MAX       = 31    # 2^5 - 1
M_SELECTOR_RESET_S   = 1     # seconds before auto-reset to 0

# ── Modbus base addresses (0-based) ──────────────────────────────────────────
I_MODBUS_START  = 0
Q_MODBUS_START  = 8192
M_MODBUS_START  = 8256
V_MODBUS_START  = 0
AI_MODBUS_START = 0
AQ_MODBUS_START = 512
VW_MODBUS_START = 0
AM_MODBUS_START = 528

# ── HA platforms ──────────────────────────────────────────────────────────────
PLATFORM_BINARY_SENSOR = "binary_sensor"
PLATFORM_SWITCH        = "switch"
PLATFORM_SENSOR        = "sensor"
PLATFORM_NUMBER        = "number"
COORDINATOR            = "coordinator"
