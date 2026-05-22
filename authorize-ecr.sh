#!/bin/bash

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 571094861812.dkr.ecr.us-east-1.amazonaws.com/namegraph
