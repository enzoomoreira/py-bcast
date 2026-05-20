"""Integration tests for events, dividends, and portfolios."""

from py_bcast import bcalendar, bdividends, bdy, bportfolios, bportfolio


class TestBcalendar:
    def test_returns_events(self):
        events = bcalendar("20260101", "20260519")
        assert len(events) >= 10  # expect hundreds

    def test_narrow_range(self):
        events = bcalendar("20260515", "20260519")
        assert isinstance(events, list)


class TestBdividends:
    def test_petrobras(self):
        # CVM 9512 = Petrobras
        divs = bdividends(9512, "PETR4")
        assert len(divs) >= 1


class TestBdy:
    def test_petrobras_dy(self):
        dy = bdy(9512, "PETR4", "20250101", "20260519")
        assert len(dy) >= 1


class TestBportfolios:
    def test_returns_brokers(self):
        brokers = bportfolios()
        assert len(brokers) >= 1


class TestBportfolio:
    def test_first_broker(self):
        brokers = bportfolios()
        if brokers:
            # Get the first broker's ID from whatever field contains it
            first = brokers[0]
            # Try to find the broker ID field (likely "10087" or first numeric field)
            broker_id = None
            for v in first.values():
                if v.isdigit():
                    broker_id = v
                    break
            if broker_id:
                holdings = bportfolio(broker_id)
                assert isinstance(holdings, list)
