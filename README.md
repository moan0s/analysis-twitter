# Analysis of Twitter data

Tools and pipelines for playing around with the data of the Twitter API

# Installation

Get the code with

```
$ git clone https://github.com/moan0s/analysis-twitter
```

then move to the directory, install the dependencies and the package

```
cd analysis-twitter
pip install -r requirements.txt
pip install -e .
```

# Configuration

In order to obtain tweets you need a [Developer Account](https://developer.twitter.com/en/apply-for-access) that gives you access to Twitters API.

Once you got these you can

```
$ cp tw_analysis/config.example.py tw_analysis/config.py

```
and fill in you credentials and the Twitter-Account you want to target.
