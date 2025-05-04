def evaluate_response(response, solution):
    """Evaluate the match between the model response and the standard answer."""
    response_lower = response.lower()
    expected_answers = [f"{key}. {value}".lower() for key, value in solution.items()]
    all_correct = all(expected_answer in response_lower for expected_answer in expected_answers)
    accuracy = 1.0 if all_correct else 0.0
    return accuracy

import logging
import os
from datetime import datetime

class Logger:
    """Object-oriented logger with file rotation and timestamped log files."""
    def __init__(self, log_dir='logs', prefix='request', max_log_files=5, level=logging.INFO):
        self.log_dir = log_dir
        self.prefix = prefix
        self.max_log_files = max_log_files
        self.level = level
        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)
        self.logger.handlers = []
        self._ensure_log_dir()
        log_file_path = self._get_log_file_path()
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        self._cleanup_old_logs()

    def _ensure_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_log_file_path(self):
        log_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(self.log_dir, f'{self.prefix}_{log_time}.log')

    def _cleanup_old_logs(self):
        log_files = sorted([f for f in os.listdir(self.log_dir) if f.startswith(self.prefix) and f.endswith('.log')])
        if len(log_files) > self.max_log_files - 1:
            for old_log in log_files[:len(log_files) - (self.max_log_files - 1)]:
                try:
                    os.remove(os.path.join(self.log_dir, old_log))
                except Exception:
                    pass

    def get_logger(self):
        return self.logger