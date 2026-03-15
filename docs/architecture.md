# System Architecture

The platform is implemented as microservices coordinated through shared infrastructure and async workloads.

## Core Layers

1. Data Acquisition
2. AI Processing
3. Automation
4. Tracking
5. Analytics
6. Dashboard

## Data Flow

Crawler → Product DB  
Product DB → Arbitrage Engine  
Arbitrage → Video Generator  
Video → Renderer  
Renderer → Automation  
Automation → Click Tracker  
Click Tracker → Analytics  
Analytics → Dashboard

## Enterprise upgrade design

For the full v3 Enterprise target model and phased migration path, see [`docs/architecture-v3-enterprise.md`](./architecture-v3-enterprise.md).
