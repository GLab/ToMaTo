# -*- coding: utf-8 -*-

import ldap

import config

def log(msg):
    #syslog.openlog('glweb', 0, settings.GLBIMGMT_LOG_FACILITY)
    #syslog.syslog(msg.encode('ascii', 'backslashreplace'))
    #syslog.closelog()
    print msg

def ldap_conn():
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, config.auth_ldap_server_cert)
    try:
        conn = ldap.initialize(uri=config.auth_ldap_server_uri)
        conn.simple_bind(who=config.auth_ldap_binddn,
                         cred=config.auth_ldap_bindpw)
    except ldap.LDAPError, error_message:
        raise Exception('Error binding to %s as %s: %s' % \
                        (config.auth_ldap_server_uri,
                         config.auth_ldap_binddn, str(error_message)))
    return conn

class LdapUser(object):
    def __init__(self, username):
        self.username = username
        self.userdn = ''

    def verify(self):
        """
        Verify if user exists. This method does NOT check a supplied password.
        """
        try:
            conn = ldap_conn()
        except Exception, e:
            log(str(e))
            return False

        try:
            user = conn.search_s(config.auth_ldap_identity_base,
                                 ldap.SCOPE_SUBTREE, 'uid=%s' % self.username)
        except Exception, e:
            log('LDAP search for user %s failed: %s' % (self.username, e))
            return False

        if len(user) > 0:
            self.userdn = user[0][0]
            ret = True
        else:
            ret = False

        try:
            conn.unbind_s()
        except Exception, e:
            log('Error closing connection to LDAP server: %s' % e)

        return ret

    def authenticate(self, password):
        """
        Check if a supplied password matches the user.
        """
        if self.verify():
            try:
                conn = ldap_conn()
            except Exception, e:
                log(str(e))
                return False

            try:
                conn = ldap.initialize(uri=config.auth_ldap_server_uri)
                conn.simple_bind_s(who=self.userdn, cred=password)
            except ldap.LDAPError, error_message:
                log('Authenticating user %s failed: %s' % (self.username,
                                                           str(error_message)))
                ret = False
            else:
                log('Authenticating user %s succeeded.' % self.username)
                ret = True

            try:
                conn.unbind_s()
            except Exception, e:
                log('Error closing connection to LDAP server: %s' % e)
        else:
            log('User %s not found.' % self.username)
            ret = False

        return ret

    def get_email_addr(self):
        try:
            conn = ldap_conn()
        except Exception, e:
            log(str(e))
            return False

        try:
            user = conn.search_s(config.auth_ldap_identity_base,
                                 ldap.SCOPE_SUBTREE, 'uid=%s' % self.username)
        except Exception, e:
            log('LDAP search for user %s failed: %s' % (self.username, e))
            return False

        if len(user) > 0:
            ret = self.email = user[0][1]['mail'][0]
        else:
            ret = None

        try:
            conn.unbind_s()
        except Exception, e:
            log('Error closing connection to LDAP server: %s' % e)

        return ret

    def is_in_group(self, group):
        if group == 'admins':
            dn = config.auth_ldap_admin_group
        elif group == 'users':
            dn = config.auth_ldap_user_group
        else:
            return False

        try:
            conn = ldap_conn()
        except Exception, e:
            log(str(e))
            return False

        try:
            members = conn.search_s(dn, ldap.SCOPE_SUBTREE, attrlist=['member'])
        except Exception, e:
            log('LDAP search for group %s failed: %s' % (group, e))
            ret = False
        else:
            if members[0][1].has_key('member'):
                if self.userdn in members[0][1]['member']:
                    ret = True
                else:
                    ret = False
            else:
                log('Group %s has no members.' % group)
                ret = False

        try:
            conn.unbind_s()
        except Exception, e:
            log('Error closing connection to LDAP server: %s' % e)

        return ret

    def is_admin(self):
        """
        Shortcut for use in templates.
        """
        return self.is_in_group('admins')

    def is_user(self):
        """
        Shortcut for use in templates.
        """
        return self.is_in_group('users')
