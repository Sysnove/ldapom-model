# LDAPOM Model

Provides base class LDAPModel create a model using [LDAPOM](https://pypi.python.org/pypi/ldapom/0.11.0).

## Installation

    pip install ldapom-model

## Example

    from ldapom-model import LDAPModel, LDAPAttr

    class Person(LDAPModel):
        _class = 'inetOrgPerson'
        _class_attrs = {'cn': LDAPAttr('cn'),
                        'o': LDAPAttr('o'),
                        'mail': LDAPAttr('mail'),
                        'lastname': LDAPAttr('sn'),
                        'firstname': LDAPAttr('givenName'),
                        'phone': LDAPAttr('telephoneNumber'),
                        'address': LDAPAttr('postalAddress')}
        _rdn = 'cn'

        def __str__(self):
            return self.name

        @property
        def name(self):
            return ' '.join([self.givenName, self.sn]) if self.givenName else self.sn


And then :

    from ldapom import LDAPConnection

    conn = LDAPConnection(uri="ldap://ldap.example.net", base="dc=example,dc=net", bind_dn="cn=root,dc=example,dc=net", bind_password="rootpassword")

    toto = Person.retrieve(conn, "toto")
    toto.mail = "toto@example.net"
    toto.firstname = "foo"
    toto.save()

    persons = Person.search(conn)

## Licence

This code is under [WTFPL](https://en.wikipedia.org/wiki/WTFPL). Just do what the fuck you want with it.

