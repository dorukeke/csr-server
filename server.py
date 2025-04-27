# Copyright (C) 2025 Doruk Eke (info@desoftware.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import zipfile

from flask import Flask, request, send_file

app = Flask(__name__)

#language="bash"
script_sh = """
#!/usr/bin/bash

openssl req -new -subj "/C={country}/CN={url}/O={organization}" \
                         -addext "subjectAltName = {subjectAltName}" \
                         -newkey rsa:4096 -keyout key.pem -out req.pem -passout "pass:"
                         
# Result keyfile somehow encrypted therefore removing encryption                          
openssl rsa -in key.pem -passin "pass:" -out key.pem
"""

default_domain_config = {
    'url': '*.desoftware.io',
    'alts': [
        'desoftware.io'
    ],
    'strength': 4096,
    'pass': '',
    'organization': 'DE Software Technologies LTD',
    'country': 'GB'
}

@app.route("/csr", methods=['POST'])
def generate_csr():
    return construct_domain_command({**default_domain_config, **request.json})


@app.route("/desoftware")
def generate_desoftware_csr():
    command = construct_domain_command(default_domain_config)
    print(command)
    return send_file(execute_command(command), as_attachment=True, download_name='csr.zip')

def execute_command(command):
    out_text = tempfile.NamedTemporaryFile()
    code = os.system(command + f' > {out_text.name}')
    if code != 0:
        return f'<h1>Failed to generate CSR<h2><p>{out_text.read()}</p>]'

    out_zip = tempfile.NamedTemporaryFile()
    zipfile2 = zipfile.ZipFile(out_zip, 'w')
    zipfile2.write('key.pem')
    zipfile2.write('req.pem')
    zipfile2.close()

    # Cleanup leftover files
    os.remove('key.pem')
    os.remove('req.pem')

    return  open(out_zip.name, "rb")

# Creates argument for OpenSSL command line for example: "DNS.1:desoftware.io,DNS.2:*.desoftware.io"
def create_openssh_subject_alt_name_arg(all_urls: list[str]):
    return ",".join(["DNS.%d:%s" % (idx + 1, i) for idx, i in enumerate(all_urls)])

def construct_domain_command(domain_config: dict):
    openssl_command_template = script_sh
    subject_alt_name = create_openssh_subject_alt_name_arg([domain_config['url'], *domain_config['alts']])

    command = openssl_command_template.format(**domain_config, subjectAltName=subject_alt_name)
    return command


def main():
    # host = '0.0.0.0'
    app.run(port=5000)


if __name__ == '__main__':
    main()

