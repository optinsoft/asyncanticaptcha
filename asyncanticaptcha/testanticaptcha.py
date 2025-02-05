from .asyncanticaptcha import AsyncAntiCaptcha, AsyncAntiCaptchaException, AsyncAntiCaptchaTimeoutException
from typing import Coroutine
import logging
from base64 import b64encode

async def testApi(apiName: str, apiRoutine: Coroutine):
    print(apiName)
    try:
        response = await apiRoutine
        print(response)
        return response
    except AsyncAntiCaptchaException as e:
        print("AsyncAntiCaptchaException:", e)
    return None

async def testImageToTextTask(anticaptcha: AsyncAntiCaptcha):
    test_file_path = "test1.jpg"
    with open(test_file_path, 'rb') as img:
        img_str = img.read()
        img_str = b64encode(img_str).decode('ascii')
    task = await anticaptcha.createImageToTextTask(img_str)
    task_status = task["status"] if "status" in task else ""
    if task_status:
        print(f"task status: {task_status}")
    if task_status == "ready":
        solution = anticaptcha.extractTaskSolution(task)
    else:
        task_id = task["taskId"]
        solution = await anticaptcha.waitForTask(task_id, log_processing=True)
    return solution["text"]

async def testAsyncAntiCaptcha(apiKey: str):
    logger = logging.Logger('testanticaptcha')

    logger.setLevel(logging.DEBUG)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    log_path = './log/test.log'

    logFormatter = logging.Formatter(log_format)
    fileHandler = logging.FileHandler(log_path)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    anticaptcha = AsyncAntiCaptcha(apiKey, logger=logger)

    print('--- asyncanticaptcha test ---')

    await testApi('getBalance', anticaptcha.getBalance())

    await testApi('imageToTextTask', testImageToTextTask(anticaptcha))
