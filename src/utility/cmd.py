import shlex
import subprocess
import logging

from src.exceptions.cmd_exceptions import CommandFailed

logger = logging.getLogger(__name__)

def exec_cmd(
    cmd,
    timeout=600,
    ignore_error=False,
    threading_lock=None,
    silent=False,
    **kwargs,
):
    """
        Run an arbitrary command locally
        If the command is grep and matching pattern is not found, then this function
        returns "command terminated with exit code 1" in stderr.
        Args:
            cmd (str): command to run
            timeout (int): Timeout for the command, defaults to 600 seconds.
            ignore_error (bool): True if ignore non zero return code and do not
                raise the exception.
            threading_lock (threading.Lock): threading.Lock object that is used
                for handling concurrent oc commands
            silent (bool): If True will silent errors from the server, default false
        Raises:
            CommandFailed: In case the command execution fails
        Returns:
            (CompletedProcess) A CompletedProcess object of the command that was executed
            CompletedProcess attributes:
            args: The list or str args passed to run().
            returncode (str): The exit code of the process, negative for signals.
            stdout     (str): The standard output (None if not captured).
            stderr     (str): The standard error (None if not captured).
    """

    logger.info(f"Executing command: {cmd}")
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    if threading_lock and cmd[0] == "oc":
        threading_lock.acquire()
    completed_process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        timeout=timeout,
        **kwargs,
    )
    if threading_lock and cmd[0] == "oc":
        threading_lock.release()
    stdout = completed_process.stdout.decode()
    stdout_err = completed_process.stderr.decode()
    if len(completed_process.stdout) > 0:
        logger.debug(f"Command stdout: {stdout}")
    else:
        logger.debug("Command stdout is empty")
    if len(completed_process.stderr) > 0:
        if not silent:
            logger.warning(f"Command stderr: {stdout_err}")
    else:
        logger.debug("Command stderr is empty")
    logger.debug(f"Command return code: {completed_process.returncode}")
    if completed_process.returncode and not ignore_error:
        if (
                "grep" in cmd
                and b"command terminated with exit code 1" in completed_process.stderr
        ):
            logger.info(f"No results found for grep command: {cmd}")
        else:
            raise CommandFailed(
                f"Error during execution of command: {cmd}."
                f"\nError is {stdout_err}"
            )
    return completed_process