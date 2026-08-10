# Amazon Ads API - release notes (excerpt)

## Version 3 overview

The Amazon Ads API uses OAuth 2.0 via Login with Amazon for authorization.
API access requires an approved developer application. Requests are scoped
to a profile, which represents an advertiser account in a specific
marketplace.

Reporting in version 3 is asynchronous: you request a report, poll its
status, then download the generated file.

## Amazon Marketing Stream

Amazon Marketing Stream delivers campaign metrics and console change
events as push-based messages to an advertiser's AWS account, using
Amazon SQS as the destination. Stream provides near real time hourly
metrics instead of pull-based report polling, and is available through
the Ads API.

## Sandbox

A sandbox environment is available for testing Sponsored Products
campaign management operations without spending real money.
