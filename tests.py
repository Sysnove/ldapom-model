#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from ldapom import LDAPConnection
from ldapom_model import LDAPModel, LDAPAttr, NoResultFound, AttributeNotFound
import ldapom
import test_server

class LDAPServerMixin(object):

    """Mixin to set up an LDAPConnection connected to a testing LDAP server."""

    def setUp(self):
        self.ldap_server = test_server.LDAPServer()
        self.ldap_server.start()
        self.ldap = LDAPConnection(
                uri=self.ldap_server.ldapi_url(),
                base='dc=example,dc=com',
                bind_dn='cn=admin,dc=example,dc=com',
                bind_password='admin')

    def tearDown(self):
        self.ldap_server.stop()


class Person(LDAPModel):
    _class = 'person'
    _class_attrs = {'cn': LDAPAttr('cn'),
                    'lastname': LDAPAttr('sn'),
                    'description': LDAPAttr('description'),
                    'invalidAttribute': LDAPAttr('invalid'),
                    'shell': LDAPAttr('loginShell'),
                    'phone': LDAPAttr('telephoneNumber', multiple=True),
                    'photo': LDAPAttr('jpegPhoto')}
    _rdn = 'cn'

    def __str__(self):
        return self.name

    @property
    def name(self):
        return ' '.join([self.givenName, self.sn]) if self.givenName else self.sn


class Test(LDAPServerMixin, unittest.TestCase):

    def test_ok(self):
        self.assertTrue(True)

    def test_retrieve(self):
        Person.retrieve(self.ldap, "jack")
        with self.assertRaises(NoResultFound):
            Person.retrieve(self.ldap, "nobody")

    def test_create(self):
        p = Person(self.ldap, 'cn=george,dc=example,dc=com', cn="george", lastname="Hammond")
        p.save()

        p = Person.retrieve(self.ldap, "george")
        self.assertEqual(p.lastname, "Hammond")

    def test_delete(self):
        p = Person.retrieve(self.ldap, "jack")
        self.assertTrue(p._entry.exists())
        p.delete()
        self.assertFalse(p._entry.exists())

    def test_new_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        p.description = "Test user"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.description, "Test user")

    def test_new_invalid_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        with self.assertRaises(ldapom.error.LDAPAttributeNameNotFoundError):
            p.invalidAttribute = 'invalid'

    def test_modify_single_value_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "/bin/bash")
        p.shell = "/bin/zsh"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "/bin/zsh")
        p.shell = ""
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.shell, "")
        p.shell = None
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        with self.assertRaises(AttributeNotFound):
            p.shell

    def test_modify_multi_value_attribute(self):
        p = Person.retrieve(self.ldap, "jack")
        p.phone = "0000000000"
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000"})
        p.phone = ["0000000000", "1111111111"]
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000", "1111111111"})
        p.phone.add("2222222222")
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, {"0000000000", "1111111111", "2222222222"})
        p.phone = []
        p.save()
        p = Person.retrieve(self.ldap, "jack")
        self.assertEqual(p.phone, set())

    def test_search(self):
        pass

    def test_search_empty_result(self):
        pass

    def test_retrieve_operational_attributes(self):
        pass

    #def test_set_binary_attribute(self):
        #p = Person.retrieve(self.ldap, "daniel")
        #jpeg = b'\xff\xd8\xff\xe0\x00\x10\xff'
        #p.photo = jpeg
        #p.save()
        #p = Person.retrieve(self.ldap, "daniel")
        #p.assertEqual(p.photo, jpeg)

if __name__ == '__main__':
    unittest.main()
