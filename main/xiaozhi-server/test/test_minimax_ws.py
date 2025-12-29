#!/usr/bin/env python3
"""
Standalone test script for MiniMax WebSocket TTS API
Usage: python test_minimax_ws.py
"""

import os
import json
import asyncio
import websockets

# Configuration
API_KEY = os.environ.get("MINIMAX_API_KEY", "your_api_key_here")
WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"

async def test_minimax_ws():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    
    print(f"Connecting to {WS_URL}...")
    
    async with websockets.connect(WS_URL, additional_headers=headers) as ws:
        # Wait for connected_success
        msg = await ws.recv()
        print(f"Received: {msg}")
        response = json.loads(msg)
        if response.get("event") != "connected_success":
            print(f"ERROR: Expected connected_success, got: {response}")
            return
        
        # Send task_start
        task_start = {
            "event": "task_start",
            "model": "speech-2.6-turbo",
            "voice_setting": {
                "voice_id": "female-shaonv",  # Use standard voice
                "speed": 1,
                "vol": 1,
                "pitch": 0,
                "emotion": "happy",
            },
            "audio_setting": {
                "sample_rate": 16000,
                "format": "pcm",
                "channel": 1,
            },
        }
        print(f"Sending task_start: {json.dumps(task_start, ensure_ascii=False)}")
        await ws.send(json.dumps(task_start))
        
        # Wait for task_started
        msg = await ws.recv()
        print(f"Received: {msg}")
        response = json.loads(msg)
        if response.get("event") != "task_started":
            print(f"ERROR: Expected task_started, got: {response}")
            return
        
        # Send task_continue with text
        task_continue = {
            "event": "task_continue",
            "text": "你好，这是一个测试。",
        }
        print(f"Sending task_continue: {json.dumps(task_continue, ensure_ascii=False)}")
        await ws.send(json.dumps(task_continue))
        
        # Wait for audio responses
        print("Waiting for audio responses...")
        audio_count = 0
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                response = json.loads(msg)
                
                event = response.get("event")
                if event == "task_failed":
                    print(f"ERROR: Task failed: {response}")
                    break
                elif event == "task_finished":
                    print("Task finished")
                    break
                elif "data" in response and "audio" in response["data"]:
                    audio_hex = response["data"]["audio"]
                    is_final = response.get("is_final", False)
                    audio_count += 1
                    print(f"Received audio chunk #{audio_count}, len={len(audio_hex) if audio_hex else 0}, is_final={is_final}")
                    if is_final:
                        print("Received final audio chunk")
                        break
                else:
                    print(f"Unknown response: {response}")
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
        
        # Send task_finish
        print("Sending task_finish...")
        await ws.send(json.dumps({"event": "task_finish"}))
        
        # Wait for task_finished response
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"After task_finish received: {msg}")
        except asyncio.TimeoutError:
            print("No response after task_finish (timeout)")
        
        print(f"=== Round 1 completed. Total audio chunks: {audio_count} ===")
        
        # Test: Can we start a new task on the same connection?
        print("\n=== Starting Round 2 (test connection reuse) ===")
        
        task_start2 = {
            "event": "task_start",
            "model": "speech-2.6-turbo",
            "voice_setting": {
                "voice_id": "female-shaonv",
                "speed": 1,
                "vol": 1,
                "pitch": 0,
                "emotion": "happy",
            },
            "audio_setting": {
                "sample_rate": 16000,
                "format": "pcm",
                "channel": 1,
            },
        }
        print(f"Sending task_start for round 2...")
        await ws.send(json.dumps(task_start2))
        
        # Wait for task_started
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"Round 2 response: {msg}")
            response = json.loads(msg)
            if response.get("event") == "task_started":
                print("SUCCESS: Can reuse connection after task_finish!")
                
                # Send another text
                await ws.send(json.dumps({"event": "task_continue", "text": "第二轮测试。"}))
                
                # Receive audio
                audio_count2 = 0
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=10)
                        response = json.loads(msg)
                        if "data" in response and "audio" in response["data"]:
                            audio_count2 += 1
                            is_final = response.get("is_final", False)
                            print(f"Round 2 audio chunk #{audio_count2}, is_final={is_final}")
                            if is_final:
                                break
                        elif response.get("event") == "task_failed":
                            print(f"Round 2 task failed: {response}")
                            break
                    except asyncio.TimeoutError:
                        print("Round 2 timeout")
                        break
                
                print(f"Round 2 completed. Audio chunks: {audio_count2}")
            else:
                print(f"Round 2 failed: {response}")
        except asyncio.TimeoutError:
            print("Round 2 timeout waiting for task_started")

if __name__ == "__main__":
    asyncio.run(test_minimax_ws())

