import configparser


class EMSXAPIConfig:

    def __init__(self, cfg_file_name=None):
        if cfg_file_name is None or len(cfg_file_name) == 0:
            cfg_file_name = 'config.cfg'

        config = configparser.RawConfigParser()
        config.read(cfg_file_name)
        config_dict = dict(config.items('Auth Config Section'))

        # read config items
        self.user = config_dict.get('user', '')
        self.password = config_dict.get('password', '')
        self.server = config_dict.get('server', '')
        self.domain = config_dict.get('domain', '')
        self.port = int(config_dict.get('port', '9000'))
        self.locale = config_dict.get('locale', '')
        self.certFilePath = config_dict.get('cert_file_path', '')
        self.ssl = config_dict.get('ssl', 'false').lower() == 'true'
        self.srpLogin = config_dict.get('srp_login', 'false').lower() == 'true'
        self.keepAliveTime = int(config_dict.get('keep_alive_time', '3600000'))
        self.keepAliveTimeout = int(config_dict.get('keep_alive_timeout', '30000'))
        self.maxRetryCount = int(config_dict.get('max_retry_count', '3'))
        self.retryDelayMS = int(config_dict.get('retry_delay_ms', '1000'))
        self.maxMessageSize = 104*1024*1024