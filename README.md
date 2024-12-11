# Ralph Asset Management Deployment (DRAFT)

**Status:** This README is currently in draft mode and subject to change.

## Overview

This repository contains our DevOps bootcamp capstone project, focusing on the deployment and configuration of **Ralph**, an open-source asset management, DCIM, and CMDB tool. Our team has worked together to showcase a fully functional, end-to-end DevOps pipeline, from infrastructure provisioning to continuous integration and continuous delivery.

Ralph provides a comprehensive solution for tracking IT assets, including hardware, software, and network infrastructure. It integrates with a variety of workflows and tools, offering robust lifecycle management and flexible customization to fit an organization’s unique needs.

[ insert team logo or image here ]

## Project Scope

Our deployment covers a wide range of operational components, including:
- **IT Hardware & Software Management**: Laptops, monitors, servers, racks, network devices.
- **Configuration & Lifecycle Tracking**: Domains, IP addresses, DHCP/DNS setups, and more.
- **Licensing & Compliance**: Managing software licenses, operational documentation, and compliance reporting.
- **Security & Automation**: Integrating security scans, automated asset transitions, and workflows.

[ insert here details about errors you faced or lessons learned ]

## Infrastructure Layout

We leverage Terraform to provision and manage our cloud resources. The infrastructure includes:

### Networking (VPC Module)
- Custom VPC with `10.0.0.0/16` CIDR.
- Multiple Availability Zones for high availability.
- Public and Private subnets, plus NAT and Internet Gateways.
- VPC Peering with the default VPC for extended network reach.

### Compute (EC2 Module)
- Private EC2 instances running the Ralph application.
- Public-facing bastion hosts for secure management access.
- Security groups strictly controlling traffic flow.
- Ubuntu-based images with automated Docker and monitoring setup.
- `t3.medium` instances chosen for cost-effectiveness and performance balance.

### Database (RDS Module)
- MySQL 5.7 RDS instance for the Ralph database.
- Multi-AZ Redis deployment for caching.
- Private subnet placement for enhanced security.
- Automated backups and routine maintenance.
- `db.t3.micro` instance type to maintain budget constraints.

### Load Balancing (ALB Module)
- Application Load Balancer distributing traffic to application instances.
- Health checks configured against the `/login/` endpoint (Ralph).
- Health checks configured against the `/metrics/` endpoint (cAdvisor and Node exporter).
- HTTP listener on port `80` `8080`, `9100`.
- Target groups for clean traffic segmentation and stickiness.

## Docker Setup

Our Docker-based deployment integrates all essential services:

- **web**: Ralph’s Django application on port `8000`.
- **nginx**: Reverse proxy and static file server on port `80`.
- **db**: Amazon RDS endpoint.
- **redis**: Amazon Redis endpoint.
- **cAdvisor**: Container level monitoring tool.
We have persistent volumes for data, media, and static assets, along with robust health checks for service reliability.

[ insert image here of x..y..z, e.g., architectural diagram ]

## CI/CD & Automation

We are leveraging Jenkins for our CI/CD pipeline:
- **Jenkins Manager EC2**: Orchestrates build and deployment jobs.
- **Jenkins Node EC2**: Builds, tests, and deploys our application changes.

Changes are currently tested in a personal forked repository before being merged into the main repository to reduce disruption to the team’s workflow. 

[ insert here more details about current testing procedures or pipeline steps ]

## Budget & Resource Constraints

We are committed to operating within a $200 AWS budget for this project. Thus far, we’ve utilized approximately $120. Careful resource planning and instance sizing have helped keep costs in check.

## Team Contributors

Our team’s roles:
- **Release Manager**: Overseeing deployment pipelines and risk management.
- **AI Chatbot Developer**: Integrating chat functionalities into Ralph.
- **IaC/Infrastructure Specialist**: Terraform scripting, AWS provisioning.
- **System Administrator**: Monitoring, logging, and alerting mechanisms.

[ insert team member names or acknowledgments ]

## Next Steps

- Add a finalized diagram of our environment.
- Document common troubleshooting steps.
- Finalize CI/CD pipeline details and link to Jenkins job examples.
- Include instructions for running and testing Ralph locally.

**This README is a work-in-progress.** As we iterate, we’ll add more details, visuals, and clarifications to ensure this resource becomes an informative guide for both our team and future stakeholders.

