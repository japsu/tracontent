# Content management system for Tracon 2016 and forwards

Too long have we suffered of Wordpress, Drupal and PencilBlue. We shall have content! And we shall be content!

## Getting started

Install dependencies:

    virtualenv venv-tracontent
    source venv-tracontent/bin/activate
    git clone https://github.com/tracon/tracontent.git
    cd tracontent
    pip install -r requirements.txt

Setup basic example content:

    ./manage.py setup --test
    ./manage.py setup_example_content 127.0.0.1:8001

Run the server and view the site in your favourite web browser:

    ./manage.py runserver 127.0.0.1:8001
    iexplore http://127.0.0.1:8001

Note that due to multisite support, `127.0.0.1:8001` needs to match whatever `host:port` you use to access your development instance.

## Kompassi OAuth2 Enabled

For more information, see the [Kompassi OAuth2 Example](/tracon/kompassi-oauth2-example).

## License

    The MIT License (MIT)

    Copyright (c) 2014–2015 Santtu Pajukanta

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
