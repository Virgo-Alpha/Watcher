#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { WatcherStack } from '../lib/watcher-stack';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load .env file from project root (two levels up from cdk/bin)
dotenv.config({ path: path.resolve(__dirname, '../../..', '.env') });

const app = new cdk.App();

new WatcherStack(app, 'WatcherStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});
