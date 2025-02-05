import aiohttp
import ssl
import certifi
import json
import logging
from functools import reduce
from datetime import datetime
import asyncio

class AsyncAntiCaptchaException(Exception):
    pass

class AsyncAntiCaptchaTimeoutException(AsyncAntiCaptchaException):
    pass

class AsyncAntiCaptchaBadStatusException(AsyncAntiCaptchaException):
    pass

class AsyncAntiCaptchaNoSolutionException(AsyncAntiCaptchaException):
    pass

class AsyncAntiCaptcha:
    def __init__(self, client_key: str, soft_id: int = 0, callback_url: str = None, api_url: str = 'https://api.anti-captcha.com/', 
                 logger: logging.Logger = None, http_timeout: int = 15, task_timeout: int = 120, get_result_delay: int = 5):
        self.client_key = client_key
        self.soft_id = soft_id
        self.callback_url = callback_url
        self.api_url = api_url
        self.logger = logger
        self.http_timeout = http_timeout        
        self.task_timeout = task_timeout
        self.get_result_delay = get_result_delay
        self.phrase = False
        self.case = False
        self.numeric = 0
        self.math = False
        self.minLength = 0
        self.maxLength = 0
        self.comment = False

    def checkResponse(self, respJson: dict):
        if respJson["errorId"] == 0:
            return respJson
        error_code = respJson["errorCode"] if "errorCode" in respJson else -1
        error_description = respJson["errorDescription"] if "errorDescription" in respJson else "Unknown error. " + json.dumps(respJson)
        raise AsyncAntiCaptchaException(f"API error {error_code}: {error_description}")

    def logRequest(self, method: str, query: dict, response: dict):
        if not self.logger is None:
            self.logger.debug(
                'method: '+method+
                ', query: '+json.dumps(query)+
                ', response '+json.dumps(response)
            )

    async def doRequest(self, method: str, query: dict):
        url = self.api_url + method
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=conn, raise_for_status=False, timeout=aiohttp.ClientTimeout(total=self.http_timeout)) as session:
            async with session.post(url, data=json.dumps(query), timeout=self.http_timeout) as resp:
                if resp.status != 200:
                    respText = await resp.text()
                    self.logRequest(method, query, {'status':resp.status,'text':respText})
                    raise AsyncAntiCaptchaException(f"Request failed:\nStatus Code: {resp.status}\nText: {respText}")
                try:
                    respText = await resp.text()
                    self.logRequest(method, query, {'status':resp.status,'text':respText})
                    respJson = json.loads(respText)
                except ValueError as e:
                    raise AsyncAntiCaptchaException(f"Request failed: {str(e)}")
                return self.checkResponse(respJson)

    async def getBalance(self):
        method = "getBalance"
        query = {"clientKey": self.client_key}
        balance = await self.doRequest(method, query)
        return balance["balance"]
    
    async def createTask(self, task_data: dict):
        method = "createTask"
        query = {
            "clientKey": self.client_key, 
            "task": task_data,
            "softId": self.soft_id
        }
        if self.callback_url:
            query["callbackUrl"] = self.callback_url
        return await self.doRequest(method, query)
    
    async def getTaskResult(self, task_id):
        method = "getTaskResult"
        query = {
            "clientKey": self.client_key,
            "taskId": task_id
        }
        return await self.doRequest(method, query)
    
    def extractTaskSolution(self, task_result):
        if not "solution" in task_result:
            raise AsyncAntiCaptchaNoSolutionException(f"no solution: {json.dumps(task_result)}")
        return task_result["solution"]
    
    async def waitForTask(self, task_id, timeout: int = 0, get_result_delay: int = 0, log_processing: bool = False):
        if timeout == 0:
            timeout = self.task_timeout
        if get_result_delay == 0:
            get_result_delay = self.get_result_delay
        if get_result_delay <= 0:
            get_result_delay = 5
        t0 = datetime.now()
        noresult = True
        task_result = {}
        while noresult:
            await asyncio.sleep(get_result_delay)
            task_result = await self.getTaskResult(task_id)
            task_status = task_result["status"] if "status" in task_result else ""
            if task_status == "ready":
                noresult = False
            elif task_status == "processing":                
                noresult = True
                if log_processing:
                    if not self.logger is None:
                       self.logger.debug("processing...")
            else:
                raise AsyncAntiCaptchaBadStatusException(f"bad task result status: {task_status}")
            if noresult:
                now = datetime.now()
                if (now-t0).total_seconds() >= timeout:
                    raise AsyncAntiCaptchaTimeoutException("resolve captcha timed out")
        return self.extractTaskSolution(task_result)

    async def createImageToTextTask(self, img_str: str):
        task_data = {
            "type": "ImageToTextTask",
            "body": img_str,
            "phrase": self.phrase,
            "case": self.case,
            "numeric": self.numeric,
            "math": self.math,
            "minLength": self.minLength,
            "maxLength": self.maxLength,
            "comment": self.comment
        }
        return await self.createTask(task_data)
