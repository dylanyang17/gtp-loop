// SPDX-License-Identifier: BSD-2-Clause
// Copyright (c) 2026 gtp-loop contributors.
// The Python helper provides `subscribers` through stdin.

function equal(a, b) {
    if (typeof a === 'string' && typeof b === 'string') {
        return a.toLowerCase() === b.toLowerCase();
    }
    return a === b;
}

function verify(actual, expected) {
    for (const field of ['k', 'op', 'opc', 'amf']) {
        if (!equal(actual.security?.[field] ?? null, expected.security[field])) {
            throw new Error('Existing subscriber ' + expected.imsi + ' has different ' + field);
        }
    }
    if (actual.subscriber_status !== 0) {
        throw new Error('Existing subscriber ' + expected.imsi + ' is not enabled');
    }
    for (const slice of expected.slice) {
        const found = actual.slice?.find(s => s.sst === slice.sst && equal(s.sd ?? null, slice.sd ?? null));
        for (const session of slice.session) {
            const configured = found?.session?.find(s => s.name === session.name);
            // IPv4v6 subscriptions also allow the bundled IPv4 UE sessions.
            if (!configured || ![1, 3].includes(configured.type) ||
                ('lbo_roaming_allowed' in session && configured.lbo_roaming_allowed === true)) {
                throw new Error('Existing subscriber ' + expected.imsi + ' has different session settings');
            }
        }
    }
    for (const number of expected.msisdn) {
        if (!actual.msisdn?.includes(number)) {
            throw new Error('Existing subscriber ' + expected.imsi + ' has a different MSISDN');
        }
    }
}

// Validate every existing user before inserting any missing user.
for (const expected of subscribers) {
    const actual = db.subscribers.findOne({imsi: expected.imsi});
    if (actual) verify(actual, expected);
}
for (const expected of subscribers) {
    const document = {...expected, security: {...expected.security, sqn: Long('0')}};
    db.subscribers.updateOne({imsi: expected.imsi}, {$setOnInsert: document}, {upsert: true});
    verify(db.subscribers.findOne({imsi: expected.imsi}), expected);
    print('Open5GS subscriber ready: ' + expected.imsi);
}
