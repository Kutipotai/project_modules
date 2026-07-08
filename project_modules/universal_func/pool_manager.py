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

        self.print_log = False
        self.print_error = False

        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._old_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, _) -> None:
        """Обработчик сигналов"""
        if self.print_log:
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
        if self.print_log:
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
            if self.print_log:
                print(f"[{self.__class__.__name__}] Skipping task submission - manager is shutting down")
            return None

        # Проверяем предыдущий результат
        if self.current_future and self.current_future.done():
            try:
                result = self.current_future.result()
                self._on_task_complete(result)
            except Exception as e:
                if self.print_error:
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
        if self.print_log:
            print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки"""
        if self.print_error:
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
            if self.print_log:
                print(f"[{self.__class__.__name__}] Manager is shutting down, skipping run {self.shutdown_flag.is_set()=}")
            return None

        # Проверяем, не выполняется ли уже задача
        if self.current_future and not self.current_future.done():
            if self.print_log:
                print(f"[{self.__class__.__name__}] Task is already running, skipping")
            return self.current_future

        # Получаем параметры и запускаем задачу
        params = self.get_task_params()
        if not params and not kwargs:
            if self.print_error:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None
        if kwargs:
            params.update(kwargs)
            if self.print_log:
                print(f"[{self.__class__.__name__}] Running with kwargs params")
        fn = params.pop('fn', None)
        if not fn:
            if self.print_log:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None

        return self._submit_task(fn, **params)

    def loop_run(self, interval: float = 60.0) -> None:
        """
        Бесконечный цикл выполнения задачи с заданным интервалом.

        Args:
            interval: Интервал между запусками в секундах
        """
        if self.print_log:
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
                if self.print_error:
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
        self.shutdown_flag = threading.Event()
        self.current_future: Optional[Future] = None
        self.running = True
        self.last_run_time = 0
        self.last_result = None

        self.print_log = False
        self.print_error = False

        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._old_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, _) -> None:
        """Обработчик сигналов"""
        if self.print_log:
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
                    if self.print_log:
                        print(f"[{self.__class__.__name__}] Killing child process {child.pid}")
                    child.terminate()
                    child.wait(timeout=1)  # <-- ИСПРАВЛЕНО: wait() вместо join()
                    if child.is_running():
                        child.kill()
                        child.wait(timeout=1)  # <-- ИСПРАВЛЕНО: wait() вместо join()
                except Exception as e:
                    if self.print_error:
                        print(f"[{self.__class__.__name__}] Error killing process {child.pid}: {e}")
        except Exception as e:
            if self.print_error:
                print(f"[{self.__class__.__name__}] Error getting children: {e}")
        if self.print_log:
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
            if self.print_log:
                print(f"[{self.__class__.__name__}] Skipping task submission - manager is shutting down")
            return None

        # Проверяем предыдущий результат
        if self.current_future and self.current_future.done():
            try:
                result = self.current_future.result()
                self._on_task_complete(result)
            except Exception as e:
                if self.print_error:
                    print(f'[{self.__class__.__name__}] Exception in previous task: {e}')
                self._on_task_error(e)

        # Отправляем новую задачу
        try:
            self.current_future = self.executor.submit(fn, *args, **kwargs)
            self.current_future.add_done_callback(self._on_future_done)
            return self.current_future
        except Exception as e:
            if self.print_error:
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
                if self.print_log:
                    print(f"[{self.__class__.__name__}] Task interrupted by shutdown")
            except Exception as e:
                if self.print_error:
                    print(f"[{self.__class__.__name__}] Exception in previous task: {e}")
                self._on_task_error(e)

    def _on_task_complete(self, result) -> None:
        """Обработка успешного завершения"""
        self.last_result = result
        self.last_run_time = time.time()
        if self.print_log:
            print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки"""
        if self.print_error:
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
            if self.print_log:
                print(f"[{self.__class__.__name__}] Manager is shutting down, skipping run")
            return None

        if self.current_future and not self.current_future.done():
            if self.print_log:
                print(f"[{self.__class__.__name__}] Task is already running, skipping")
            return self.current_future

        params = self.get_task_params()
        if not params and not kwargs:
            if self.print_error:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None

        if kwargs:
            params.update(kwargs)
            if self.print_log:
                print(f"[{self.__class__.__name__}] Running with kwargs params")

        fn = params.pop('fn', None)
        if not fn:
            if self.print_error:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None

        return self._submit_task(fn, **params)

    def loop_run(self, interval: float = 60.0) -> None:
        if self.print_log:
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
                if self.print_error:
                    print(f'[{self.__class__.__name__}] Error in loop: {e}')
                if not self.shutdown_flag.is_set():
                    time.sleep(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class BaseProcessPoolManagerV2(ABC):
    """Базовый класс для управления ProcessPoolExecutor с graceful shutdown"""

    def __init__(
        self,
        max_workers: int = 1,
        shutdown_pool_after_task: bool = False,
        **kwargs,
    ):
        self.max_workers = max_workers
        self.shutdown_pool_after_task = shutdown_pool_after_task

        self.executor: Optional[ProcessPoolExecutor] = None
        self._ensure_executor()

        self.shutdown_flag = threading.Event()
        self.current_future: Optional[Future] = None
        self.running = True
        self.last_run_time = 0
        self.last_result = None

        self.print_log = False
        self.print_error = False

        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._old_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

    def _ensure_executor(self) -> None:
        """Создает ProcessPoolExecutor при необходимости."""
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)

    def _shutdown_executor(self) -> None:
        """Закрывает только ProcessPoolExecutor."""
        if self.executor is None:
            return

        try:
            self.executor.shutdown(wait=False, cancel_futures=False)
            if self.print_log:
                print(f"[{self.__class__.__name__}] shutdown_executor complete")
        except Exception as e:
            if self.print_log:
                print(f"[{self.__class__.__name__}] shutdown_executor Error! {e}")
            pass
        finally:
            self.executor = None

    def _kill_child_processes(self) -> None:
        """
        Аварийное завершение всех дочерних процессов текущего процесса.

        Используется только при полном shutdown() приложения.
        Не вызывается при shutdown_pool_after_task, чтобы не завершать
        процессы других ProcessPoolExecutor'ов.
        """
        try:
            parent = psutil.Process()

            for child in parent.children(recursive=True):
                try:
                    if self.print_log:
                        print(f"[{self.__class__.__name__}] Killing child process {child.pid}")

                    child.terminate()
                    child.wait(timeout=1)

                    if child.is_running():
                        child.kill()
                        child.wait(timeout=1)

                except Exception as e:
                    if self.print_error:
                        print(
                            f"[{self.__class__.__name__}] "
                            f"Error killing process {child.pid}: {e}"
                        )

        except Exception as e:
            if self.print_error:
                print(f"[{self.__class__.__name__}] Error getting children: {e}")

    def _signal_handler(self, signum: int, _) -> None:
        """Обработчик сигналов."""
        if self.print_log:
            print(f"[{self.__class__.__name__}] Received signal {signum}, shutting down...")

        self.shutdown()
        raise KeyboardInterrupt()

    def shutdown(self) -> None:
        """Полное завершение менеджера."""
        self.running = False
        self.shutdown_flag.set()

        if self.current_future and not self.current_future.done():
            self.current_future.cancel()

        self._shutdown_executor()
        self._kill_child_processes()

        if self.print_log:
            print(f"[{self.__class__.__name__}] Shutdown complete")

    def cleanup(self) -> None:
        """Очистка ресурсов."""
        if self.running:
            self.shutdown()

        signal.signal(signal.SIGINT, self._old_sigint)
        signal.signal(signal.SIGTERM, self._old_sigterm)

    def _submit_task(self, fn: Callable, *args, **kwargs) -> Optional[Future]:
        """Универсальная отправка задачи."""
        if not self.running or self.shutdown_flag.is_set():
            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Skipping task submission - manager is shutting down"
                )
            return None

        # Предыдущий результат уже обработан callback'ом.
        if self.current_future and self.current_future.done():
            self.current_future = None

        self._ensure_executor()

        try:
            self.current_future = self.executor.submit(fn, *args, **kwargs)
            self.current_future.add_done_callback(self._on_future_done)
            return self.current_future

        except Exception as e:
            if self.print_error:
                print(f"[{self.__class__.__name__}] Error submitting task: {e}")
            return None

    def _on_future_done(self, future: Future) -> None:
        """Callback при завершении задачи."""
        try:
            if future.cancelled():
                return

            result = future.result()
            self._on_task_complete(result)

        except KeyboardInterrupt:
            if self.print_log:
                print(f"[{self.__class__.__name__}] Task interrupted by shutdown")

        except Exception as e:
            if self.print_error:
                print(f"[{self.__class__.__name__}] Task failed: {e}")

            self._on_task_error(e)

        finally:
            if self.current_future is future:
                self.current_future = None

            if self.shutdown_pool_after_task:
                self._shutdown_executor()

    def _on_task_complete(self, result) -> None:
        """Обработка успешного завершения."""
        self.last_result = result
        self.last_run_time = time.time()

        if self.print_log:
            print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки."""
        if self.print_error:
            print(f"[{self.__class__.__name__}] Task failed: {error}")

    def get_last_result(self):
        return self.last_result

    def get_last_run_time(self) -> float:
        return self.last_run_time

    @abstractmethod
    def get_task_params(self) -> Dict[str, Any]:
        pass

    def one_run(self, **kwargs) -> Optional[Future]:
        if self.shutdown_flag.is_set():
            if self.print_log:
                print(f"[{self.__class__.__name__}] Manager is shutting down, skipping run")
            return None

        if self.current_future and not self.current_future.done():
            if self.print_log:
                print(f"[{self.__class__.__name__}] Task is already running, skipping")
            return self.current_future

        params = self.get_task_params()

        if not params and not kwargs:
            if self.print_error:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None

        if kwargs:
            params.update(kwargs)

            if self.print_log:
                print(f"[{self.__class__.__name__}] Running with kwargs params")

        fn = params.pop("fn", None)

        if fn is None:
            if self.print_error:
                print(f"[{self.__class__.__name__}] No task function provided")
            return None

        return self._submit_task(fn, **params)

    def loop_run(self, interval: float = 60.0) -> None:
        if self.print_log:
            print(f"[{self.__class__.__name__}] Starting loop with interval {interval}s")

        while self.running and not self.shutdown_flag.is_set():
            try:
                future = self.one_run()

                if future:
                    while not future.done() and not self.shutdown_flag.is_set():
                        time.sleep(0.1)

                if self.shutdown_flag.is_set():
                    break

                time.sleep(interval)

            except Exception as e:
                if self.print_error:
                    print(f"[{self.__class__.__name__}] Error in loop: {e}")

                if not self.shutdown_flag.is_set():
                    time.sleep(interval)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class BaseProcessPoolManagerV3(ABC):
    """Базовый класс для управления ProcessPoolExecutor с graceful shutdown"""

    def __init__(self, max_workers: int = 1, shutdown_pool_after_task: bool = False, **kwargs):
        self.max_workers = max_workers
        self.shutdown_pool_after_task = shutdown_pool_after_task
        self.executor: Optional[ProcessPoolExecutor] = None

        self.shutdown_flag = threading.Event()
        self.current_future: Optional[Future] = None

        self.running = True
        self.last_run_time = 0
        self.last_result = None

        self.print_log = False
        self.print_error = False

        self._ensure_executor()

        # Регистрируем обработчики сигналов
        self._old_sigint = signal.signal(
            signal.SIGINT,
            self._signal_handler
        )
        self._old_sigterm = signal.signal(
            signal.SIGTERM,
            self._signal_handler
        )

    def _ensure_executor(self) -> None:
        """
        Создает ProcessPoolExecutor, если он отсутствует.

        Используется для режима shutdown_pool_after_task,
        когда пул может быть закрыт после выполнения задачи.
        """
        if self.executor is None:
            self.executor = ProcessPoolExecutor(
                max_workers=self.max_workers
            )

    def shutdown_executor(self) -> None:
        """
        Штатное закрытие только ProcessPoolExecutor.

        Менеджер остается рабочим:
        - running не меняется;
        - shutdown_flag не устанавливается;
        - следующий one_run() создаст новый пул.
        """
        if self.executor is None:
            return

        try:
            self.executor.shutdown(
                wait=False,
                cancel_futures=False
            )

            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Executor shutdown complete"
                )

        except Exception as e:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Executor shutdown error: {e}"
                )

        finally:
            self.executor = None

    def stop(self) -> None:
        """
        Останавливает только текущий экземпляр менеджера.

        Без убийства дочерних процессов через psutil.
        Безопасно использовать, если существует несколько
        экземпляров BaseProcessPoolManager.
        """
        self.running = False
        self.shutdown_flag.set()

        if self.current_future and not self.current_future.done():
            self.current_future.cancel()

        self.shutdown_executor()

        if self.print_log:
            print(
                f"[{self.__class__.__name__}] "
                f"Manager stopped"
            )

    def shutdown(self) -> None:
        """
        Аварийное завершение менеджера.

        Используется:
        - SIGINT;
        - SIGTERM;
        - критическое завершение приложения.

        Помимо остановки менеджера принудительно
        завершает дочерние процессы.
        """
        self.stop()

        self._kill_child_processes()

        if self.print_log:
            print(
                f"[{self.__class__.__name__}] "
                f"Force shutdown complete"
            )

    def _kill_child_processes(self) -> None:
        """
        Аварийное завершение всех дочерних процессов.

        Используется только при полном shutdown().
        Не вызывается при shutdown_executor()
        и shutdown_pool_after_task.
        """
        try:
            parent = psutil.Process()

            for child in parent.children(recursive=True):
                try:
                    if self.print_log:
                        print(
                            f"[{self.__class__.__name__}] "
                            f"Killing child process {child.pid}"
                        )

                    child.terminate()
                    child.wait(timeout=1)

                    if child.is_running():
                        child.kill()
                        child.wait(timeout=1)

                except Exception as e:
                    if self.print_error:
                        print(
                            f"[{self.__class__.__name__}] "
                            f"Error killing process {child.pid}: {e}"
                        )

        except Exception as e:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Error getting children: {e}"
                )

    def _signal_handler(self, signum: int, _) -> None:
        """
        Обработчик системных сигналов.

        Здесь используем полный shutdown,
        так как это аварийное завершение приложения.
        """
        if self.print_log:
            print(
                f"[{self.__class__.__name__}] "
                f"Received signal {signum}, shutting down..."
            )

        self.shutdown()
        raise KeyboardInterrupt()

    def cleanup(self) -> None:
        """
        Безопасная очистка ресурсов.

        Не убивает чужие дочерние процессы.
        """
        if self.running:
            self.stop()

        # Восстанавливаем обработчики сигналов
        signal.signal(signal.SIGINT, self._old_sigint)
        signal.signal(signal.SIGTERM, self._old_sigterm)

    def _submit_task(self, fn: Callable, *args, **kwargs) -> Optional[Future]:
        """
        Универсальная отправка задачи.
        """

        if not self.running or self.shutdown_flag.is_set():
            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Skipping task submission - manager is shutting down"
                )

            return None

        # Если предыдущий Future завершился,
        # его результат уже обработан через callback.
        if self.current_future and self.current_future.done():
            self.current_future = None

        # В режиме shutdown_pool_after_task
        # executor может быть закрыт после предыдущего запуска.
        self._ensure_executor()

        try:
            self.current_future = self.executor.submit(
                fn,
                *args,
                **kwargs
            )

            self.current_future.add_done_callback(
                self._on_future_done
            )

            return self.current_future

        except Exception as e:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Error submitting task: {e}"
                )

            return None

    def _on_future_done(self, future: Future) -> None:
        """
        Callback при завершении задачи.
        """

        try:
            if future.cancelled():
                return

            result = future.result()

            self._on_task_complete(result)

        except KeyboardInterrupt:
            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Task interrupted by shutdown"
                )

        except Exception as e:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Task failed: {e}"
                )

            self._on_task_error(e)

        finally:
            # Убираем ссылку только на этот Future.
            # Защита от ситуации, когда уже запустили новый.
            if self.current_future is future:
                self.current_future = None

            # Закрываем пул после задачи,
            # но не останавливаем менеджер.
            if self.shutdown_pool_after_task:
                self.shutdown_executor()

    def _on_task_complete(self, result) -> None:
        """Обработка успешного завершения."""
        self.last_result = result
        self.last_run_time = time.time()

        if self.print_log:
            print(f"[{self.__class__.__name__}] Task completed successfully")

    def _on_task_error(self, error: Exception) -> None:
        """Обработка ошибки."""
        if self.print_error:
            print(f"[{self.__class__.__name__}] Task failed: {error}")

    def get_last_result(self):
        return self.last_result

    def get_last_run_time(self) -> float:
        return self.last_run_time

    @abstractmethod
    def get_task_params(self) -> Dict[str, Any]:
        pass

    def one_run(self, **kwargs) -> Optional[Future]:
        """
        Запускает одну задачу.

        Если задача уже выполняется —
        возвращает текущий Future.
        """

        if self.shutdown_flag.is_set():
            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Manager is shutting down, skipping run"
                )

            return None

        # Не запускаем параллельные задачи.
        if self.current_future and not self.current_future.done():
            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Task is already running, skipping"
                )

            return self.current_future

        params = self.get_task_params()

        if not params and not kwargs:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"No task function provided"
                )

            return None

        if kwargs:
            params.update(kwargs)

            if self.print_log:
                print(
                    f"[{self.__class__.__name__}] "
                    f"Running with kwargs params"
                )

        fn = params.pop("fn", None)

        if fn is None:
            if self.print_error:
                print(
                    f"[{self.__class__.__name__}] "
                    f"No task function provided"
                )

            return None

        return self._submit_task(
            fn,
            **params
        )

    def loop_run(self, interval: float = 60.0) -> None:
        """
        Периодический запуск задач.
        """

        if self.print_log:
            print(
                f"[{self.__class__.__name__}] "
                f"Starting loop with interval {interval}s"
            )

        while self.running and not self.shutdown_flag.is_set():

            try:
                future = self.one_run()

                if future:
                    while (
                            not future.done()
                            and not self.shutdown_flag.is_set()
                    ):
                        time.sleep(0.1)

                if self.shutdown_flag.is_set():
                    break

                time.sleep(interval)

            except Exception as e:
                if self.print_error:
                    print(
                        f"[{self.__class__.__name__}] "
                        f"Error in loop: {e}"
                    )

                if not self.shutdown_flag.is_set():
                    time.sleep(interval)

    def __enter__(self):
        return self

    def __exit__(
            self,
            exc_type,
            exc_val,
            exc_tb
    ):
        self.cleanup()

