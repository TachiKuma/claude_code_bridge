import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:test/test.dart';

void main() {
  test('push route requires a complete paired target', () {
    expect(
      () => PushNotificationRoute.fromData(const {'route_project_id': 'demo'}),
      throwsFormatException,
    );

    final route = PushNotificationRoute.fromData(const {
      'route_project_id': 'proj-demo',
      'route_agent': 'mobile',
      'host_id': 'host-demo',
      'device_id': 'device-demo',
    });

    expect(route.matches(_host()), isTrue);
    expect(route.matches(_host(deviceId: 'other-device')), isFalse);
  });

  test('permission denial leaves push unregistered and route-free', () async {
    final messaging = _FakePushMessagingClient(permissionGranted: false);
    final routes = <PushNotificationRoute>[];
    final runtime = PushNotificationRuntime(
      messaging: messaging,
      registration: GatewayPushRegistrationClient(isEnabled: () => true),
      onRouteOpened: (route) async => routes.add(route),
      isEnabled: () => true,
    );

    expect(await runtime.start(_host()), isFalse);
    expect(messaging.tokenReads, 0);
    expect(routes, isEmpty);

    await runtime.dispose();
  });

  test('missing native Firebase configuration fails closed', () async {
    final messaging = FirebasePushMessagingClient();

    expect(await messaging.initializeAndRequestPermission(), isFalse);
  });

  test(
    'token refresh stays bound to the paired device and opens matching route',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final requests = <Map<String, Object?>>[];
      final subscription = server.listen((request) async {
        requests.add({
          'path': request.uri.path,
          'authorization': request.headers.value(
            HttpHeaders.authorizationHeader,
          ),
          'body': jsonDecode(await utf8.decodeStream(request)),
        });
        request.response.statusCode = HttpStatus.created;
        await request.response.close();
      });
      final messaging = _FakePushMessagingClient(token: 'first-token');
      final routes = <PushNotificationRoute>[];
      final runtime = PushNotificationRuntime(
        messaging: messaging,
        registration: GatewayPushRegistrationClient(isEnabled: () => true),
        onRouteOpened: (route) async => routes.add(route),
        isEnabled: () => true,
      );
      final host = _host(port: server.port);

      expect(await runtime.start(host), isTrue);
      messaging.refresh('second-token');
      messaging.open(
        const PushNotificationRoute(
          projectId: 'proj-demo',
          agent: 'mobile',
          hostId: 'host-demo',
          deviceId: 'device-demo',
        ),
      );
      messaging.open(
        const PushNotificationRoute(
          projectId: 'proj-demo',
          agent: 'other',
          deviceId: 'wrong-device',
        ),
      );
      await _drain();

      expect(requests, hasLength(2));
      expect(requests.first['path'], '/v1/devices/me/push');
      expect(requests.first['authorization'], 'Bearer paired-device-token');
      expect(requests.first['body'], {
        'platform': 'android',
        'device_id': 'device-demo',
        'token': 'first-token',
      });
      expect(routes.map((route) => route.agent), ['mobile']);

      await runtime.dispose();
      await subscription.cancel();
      await server.close(force: true);
    },
  );
}

GatewayPairedHost _host({String deviceId = 'device-demo', int? port}) {
  return GatewayPairedHost(
    profile: GatewayHostProfile(
      hostId: 'host-demo',
      deviceId: deviceId,
      routeProvider: RouteProvider(
        kind: RouteProviderKind.lan,
        gatewayUrl: Uri.parse('http://127.0.0.1:${port ?? 8787}'),
      ),
      scopes: const {'notify'},
    ),
    deviceToken: 'paired-device-token',
  );
}

Future<void> _drain() async {
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
}

class _FakePushMessagingClient implements PushMessagingClient {
  _FakePushMessagingClient({this.permissionGranted = true, this.token});

  final bool permissionGranted;
  final String? token;
  final _refreshes = StreamController<String>.broadcast();
  final _routes = StreamController<PushNotificationRoute>.broadcast();
  int tokenReads = 0;

  @override
  Future<PushNotificationRoute?> getInitialRoute() async => null;

  @override
  Future<String?> getToken() async {
    tokenReads += 1;
    return token;
  }

  @override
  Future<bool> initializeAndRequestPermission() async => permissionGranted;

  @override
  Stream<PushNotificationRoute> get onRouteOpened => _routes.stream;

  @override
  Stream<String> get onTokenRefresh => _refreshes.stream;

  void refresh(String token) => _refreshes.add(token);

  void open(PushNotificationRoute route) => _routes.add(route);
}
