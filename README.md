[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

# osmosis-azure-driver

> 💧 Osmosis Azure Driver Implementation
> [oceanprotocol.com](https://oceanprotocol.com)

[![Build Status](https://travis-ci.com/oceanprotocol/osmosis-azure-driver.svg)](https://travis-ci.com/oceanprotocol/osmosis-azure-driver)
[![PyPI](https://img.shields.io/pypi/v/osmosis-azure-driver.svg)](https://pypi.org/project/osmosis-azure-driver/)
[![GitHub contributors](https://img.shields.io/github/contributors/oceanprotocol/osmosis-azure-driver.svg)](https://github.com/oceanprotocol/osmosis-azure-driver/graphs/contributors)

---

## Table of Contents

- [Setup](#setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [New Version](#new-version)
- [License](#license)

---

## Setup

To use Azure Storage with Brizo, you must set up some Azure Storage and then tell Brizo about your Azure Storage account by setting some Brizo configuration settings (either in a Brizo config file or in some environment variables). For details, see:

- [the README.md file in the Brizo repository](https://github.com/oceanprotocol/brizo/blob/develop/README.md) and
- [the tutorial about how to set up Azure Storage for use with Ocean Protocol](https://docs.oceanprotocol.com/tutorials/azure-for-brizo/)

## Code Style

Information about our Python code style is documented in the [python-developer-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-developer-guide.md)
and the [python-style-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-style-guide.md).

## Testing

Automatic tests are set up via Travis, executing `tox`.
Our tests use the pytest framework.

## New Version

The `bumpversion.sh` script helps to bump the project version. You can execute the script using as first argument {major|minor|patch} to bump accordingly the version.

## License

```text
Copyright 2018 Ocean Protocol Foundation Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Note: Installing this package (osmosis-azure-driver) installs the azure package which has an MIT license. Installing the azure package installs the certifi package which has an MPL-2.0 license. The certifi source code can be found at https://github.com/certifi/python-certifi . Installing the azure package also installs the chardet package which might have licensing that is incompatible with the MIT license (and the Apache-2.0 license). We have opened [an issue](https://github.com/Azure/azure-sdk-for-python/issues/4671) on the azure-sdk-for-python repository to let them know about the potential licensing conflict and to resolve it if necessary.
