import time
import signal
import psutil
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
from typing import Optional, Callable, Any, Dict
from abc import ABC, abstractmethod


class BaseThreadPoolManager(ABC):
    """Базовый класс для управления ThreadPoolExecutor с graceful shutdown"""

    def __init__(self, max_workers: int = 1, thread_name_prefix: str = "Worker", **kwargs):
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix
        )
        self.shutdown_flag = threading.Event()
        self.current_future: Optional[Future] = None
        self.running = True
        self.last_run_time = 0
        self.last_result = None
        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._old_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, _) -> None:
        """Обработчик сигналов"""
        print(f"[{self.__class__.__name__}] Received signal {signum}, shutting down...")
        self.shutdown()
        raise KeyboardInterrupt()

    def shutdown(self) -> None:
        """Graceful shutdown"""
        self.running = False
        self.shutdown_flag.set()

        # Отменяем текущую задачу
        if self.current_future and not self.current_future.done():
            self.current_future.cancel()

        # Завершаем executor
        self.executor.shutdown(wait=False, cancel_futures=True)
        print(f"[{self.__class__.__name__}] Shutdown complete")

    def cleanup(self) -> None:
        """Очистка ресурсов (для ручного вызова)"""
        if self.running:
            self.shutdown()

        # Восстанавливаем обработчики сигналов
        signal.signal(signal.SIGINT, self._old_sigint)
        signal.signal(signal.SIGTERM, self._old_sigterm)

    def _submit_task(self, fn: Callable, *args, **kwargs) -> Optional[Future]:
        """Универсальная отправка задачи"""
        if not self.running or self.shutdown_flag.is_set():
            print(f"[{self.__class__.__name__}] Skipping task submission - manager is shutting down")
            return None

        # Проверяем предыдущий результат
        if self.current_future and self.current_future.done():
            try:
                result = self.current_future.result()
                self._on_task_complete(result)
            except Exception as e:
                print(f'[{self.__class__.__name__}] Exception in previous task: {e}')
                self._on_task_error(e)

        # Отправляем новую задачу
        try:
            self.current_future = self.executor.submit(fn, *args, **kwargs)
            # Добавляем callback для обработки результата
            self.current_future.add_done_callback(self._on_future_done)
            return self.current_future
        except Exception as e:
            print(f'[{self.__class__.__name__}] Error submitting task: {e}')
            return None

    def _on_future_done(self, future: Future) -> None:
        """Callback при завершении задачи"""
        if future.done() and not future.cancelled():
            try:
                result = future.result()
                self._on_task_complete(result)
            except Exception as e:
                self._on_task_error(e)

    def _on_task_complete(self, result) -> None:
        """Обработка успешного завершения"""
        self.last_result = result
        self.last_run_time = time.time()
        print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки"""
        print(f'[{self.__class__.__name__}] Task failed: {error}')

    def get_last_result(self):
        """Получить последний результат"""
        return self.last_result

    def get_last_run_time(self) -> float:
        """Получить время последнего запуска"""
        return self.last_run_time

    @abstractmethod
    def get_task_params(self) -> Dict[str, Any]:
        """Получение параметров для задачи"""
        pass

    def one_run(self, **kwargs) -> Optional[Future]:
        """
        Однократный запуск задачи.
        Используется, когда нужно контролировать выполнение извне.

        Returns:
            Future объект или None если задача не запущена
        """
        if self.shutdown_flag.is_set():
            print(f"[{self.__class__.__name__}] Manager is shutting down, skipping run {self.shutdown_flag.is_set()=}")
            return None

        # Проверяем, не выполняется ли уже задача
        if self.current_future and not self.current_future.done():
            print(f"[{self.__class__.__name__}] Task is already running, skipping")
            return self.current_future

        # Получаем параметры и запускаем задачу
        params = self.get_task_params()
        if not params and not kwargs:
            return None
        if kwargs:
            params.update(kwargs)
            print(f"[{self.__class__.__name__}] Running with params: {params}")
        fn = params.pop('fn', None)
        if not fn:
            print(f"[{self.__class__.__name__}] No task function provided")
            return None

        return self._submit_task(fn, **params)

    def loop_run(self, interval: float = 60.0) -> None:
        """
        Бесконечный цикл выполнения задачи с заданным интервалом.

        Args:
            interval: Интервал между запусками в секундах
        """
        print(f"[{self.__class__.__name__}] Starting loop with interval {interval}s")

        while self.running and not self.shutdown_flag.is_set():
            try:
                # Запускаем задачу
                future = self.one_run()

                # Если задача запущена, ждем её завершения
                if future and not future.done():
                    # Ждем с возможностью прерывания по shutdown_flag
                    while not future.done() and not self.shutdown_flag.is_set():
                        time.sleep(0.1)

                # Если флаг остановки установлен - выходим
                if self.shutdown_flag.is_set():
                    break

                # Пауза до следующего запуска
                time.sleep(interval)

            except Exception as e:
                print(f'[{self.__class__.__name__}] Error in loop: {e}')
                if not self.shutdown_flag.is_set():
                    time.sleep(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class BaseProcessPoolManager(ABC):
    """Базовый класс для управления ProcessPoolExecutor с graceful shutdown"""

    def __init__(self, max_workers: int = 1, **kwargs):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.shutdown_flag = threading.Event()  # threading.Event проще
        self.current_future: Optional[Future] = None
        self.running = True
        self.last_run_time = 0
        self.last_result = None

        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._old_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, _) -> None:
        """Обработчик сигналов"""
        print(f"[{self.__class__.__name__}] Received signal {signum}, shutting down...")
        self.shutdown()
        raise KeyboardInterrupt()  # <- Имитируем Ctrl+C

    def shutdown(self) -> None:
        """Graceful shutdown"""
        self.running = False
        self.shutdown_flag.set()

        if self.current_future and not self.current_future.done():
            self.current_future.cancel()

        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

        # Принудительное завершение процессов
        try:
            parent = psutil.Process()
            for child in parent.children(recursive=True):
                try:
                    print(f"[{self.__class__.__name__}] Killing child process {child.pid}")
                    child.terminate()
                    child.wait(timeout=1)  # <-- ИСПРАВЛЕНО: wait() вместо join()
                    if child.is_running():
                        child.kill()
                        child.wait(timeout=1)  # <-- ИСПРАВЛЕНО: wait() вместо join()
                except Exception as e:
                    print(f"[{self.__class__.__name__}] Error killing process {child.pid}: {e}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error getting children: {e}")

        print(f"[{self.__class__.__name__}] Shutdown complete")

    def cleanup(self) -> None:
        """Очистка ресурсов (для ручного вызова)"""
        if self.running:
            self.shutdown()

        # Восстанавливаем обработчики сигналов
        signal.signal(signal.SIGINT, self._old_sigint)
        signal.signal(signal.SIGTERM, self._old_sigterm)

    def _submit_task(self, fn: Callable, *args, **kwargs) -> Optional[Future]:
        """Универсальная отправка задачи"""
        if not self.running or self.shutdown_flag.is_set():
            print(f"[{self.__class__.__name__}] Skipping task submission - manager is shutting down")
            return None

        # Проверяем предыдущий результат
        if self.current_future and self.current_future.done():
            try:
                result = self.current_future.result()
                self._on_task_complete(result)
            except Exception as e:
                print(f'[{self.__class__.__name__}] Exception in previous task: {e}')
                self._on_task_error(e)

        # Отправляем новую задачу
        try:
            self.current_future = self.executor.submit(fn, *args, **kwargs)
            self.current_future.add_done_callback(self._on_future_done)
            return self.current_future
        except Exception as e:
            print(f'[{self.__class__.__name__}] Error submitting task: {e}')
            return None

    def _on_future_done(self, future: Future) -> None:
        """Callback при завершении задачи"""
        if future.done() and not future.cancelled():
            try:
                result = future.result()
                self._on_task_complete(result)
            except KeyboardInterrupt:
                # Игнорируем KeyboardInterrupt при завершении
                print(f"[{self.__class__.__name__}] Task interrupted by shutdown")
            except Exception as e:
                self._on_task_error(e)

    def _on_task_complete(self, result) -> None:
        """Обработка успешного завершения"""
        self.last_result = result
        self.last_run_time = time.time()
        print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки"""
        print(f'[{self.__class__.__name__}] Task failed: {error}')

    def get_last_result(self):
        return self.last_result

    def get_last_run_time(self) -> float:
        return self.last_run_time

    @abstractmethod
    def get_task_params(self) -> Dict[str, Any]:
        pass

    def one_run(self, **kwargs) -> Optional[Future]:
        if self.shutdown_flag.is_set():
            print(f"[{self.__class__.__name__}] Manager is shutting down, skipping run")
            return None

        if self.current_future and not self.current_future.done():
            print(f"[{self.__class__.__name__}] Task is already running, skipping")
            return self.current_future

        params = self.get_task_params()
        if not params and not kwargs:
            return None

        if kwargs:
            params.update(kwargs)
            print(f"[{self.__class__.__name__}] Running with params: {params}")

        fn = params.pop('fn', None)
        if not fn:
            print(f"[{self.__class__.__name__}] No task function provided")
            return None

        return self._submit_task(fn, **params)

    def loop_run(self, interval: float = 60.0) -> None:
        print(f"[{self.__class__.__name__}] Starting loop with interval {interval}s")

        while self.running and not self.shutdown_flag.is_set():
            try:
                future = self.one_run()

                if future and not future.done():
                    while not future.done() and not self.shutdown_flag.is_set():
                        time.sleep(0.1)

                if self.shutdown_flag.is_set():
                    break

                time.sleep(interval)

            except Exception as e:
                print(f'[{self.__class__.__name__}] Error in loop: {e}')
                if not self.shutdown_flag.is_set():
                    time.sleep(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

