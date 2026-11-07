package ru.mirea.ZubarevVS.lesson6.employeedb;

import android.os.Bundle;

import java.util.List;

import ru.mirea.ZubarevVS.lesson6.employeedb.databinding.ActivityMainBinding;

/**
 * Экран CRUD для героев с ID, который вводит пользователь.
 * Поля читаются в главном потоке, запросы Room выполняет последовательный исполнитель io.
 */
public class MainActivity extends BaseActivity {
    // Binding предоставляет ссылки на поля и кнопки из activity_main.xml.
    private ActivityMainBinding binding;
    // Реализацию этого интерфейса генерирует Room.
    private HeroDao dao;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        frame(binding.getRoot());

        dao = ((App) getApplication()).database().heroDao();
        binding.add.setOnClickListener(v -> change("add"));
        binding.find.setOnClickListener(v -> change("find"));
        binding.update.setOnClickListener(v -> change("update"));
        binding.delete.setOnClickListener(v -> change("delete"));
        binding.refresh.setOnClickListener(v -> change("list"));
        change("list");
    }

    /**
     * Показывает одну причину отказа и рядом с полем ID, и в области результата.
     * Метод вызывается в главном потоке, в том числе через ui() после проверки базы.
     */
    private void showIdError(String message) {
        binding.heroId.setError(message);
        binding.heroId.requestFocus();
        binding.result.setText(message);
    }

    /**
     * Порядок проверки ID: заполнение → целое число long → больше нуля.
     * Для добавления в фоне проверяется уникальность, затем записывается именно введённый ID.
     * Команда list читает всю таблицу без требования заполнить поля.
     */
    private void change(String action) {
        binding.heroId.setError(null);
        String idText = binding.heroId.getText().toString().trim();
        String name = binding.heroName.getText().toString().trim();
        String power = binding.power.getText().toString().trim();

        long id = 0;
        if (!action.equals("list")) {
            if (idText.isEmpty()) {
                showIdError(getString(R.string.error_id_required));
                return;
            }
            try {
                id = Long.parseLong(idText);
            } catch (NumberFormatException e) {
                // Дроби, буквы и значения вне диапазона long отклоняются до запроса к базе.
                showIdError(getString(R.string.error_id_integer));
                return;
            }
            if (id <= 0) {
                showIdError(getString(R.string.error_id_positive));
                return;
            }
        }
        if ((action.equals("add") || action.equals("update"))
                && (name.isEmpty() || power.isEmpty())) {
            binding.result.setText(R.string.error_hero_fields);
            return;
        }

        // Фиксируем введённый ID для фоновой задачи.
        final long target = id;
        io.execute(() -> {
            try {
                String message = "";
                if (action.equals("add")) {
                    if (dao.getById(target) != null) {
                        ui(() -> showIdError(getString(R.string.error_id_taken, target)));
                        return;
                    }
                    Hero hero = new Hero();
                    hero.id = target;
                    hero.name = name;
                    hero.power = power;
                    // Первичный ключ и INSERT IGNORE защищают от совпадения ID даже при
                    // конкурентной вставке после проверки getById. -1 означает отказ вставки.
                    if (dao.insert(hero) == -1) {
                        ui(() -> showIdError(getString(R.string.error_id_taken, target)));
                        return;
                    }
                    message = getString(R.string.hero_added, target);
                } else if (!action.equals("list")) {
                    Hero hero = dao.getById(target);
                    if (hero == null) {
                        ui(() -> showIdError(getString(R.string.error_id_missing, target)));
                        return;
                    }
                    if (action.equals("find")) {
                        ui(() -> {
                            binding.heroName.setText(hero.name);
                            binding.power.setText(hero.power);
                        });
                        message = getString(R.string.hero_found, target);
                    } else if (action.equals("update")) {
                        hero.name = name;
                        hero.power = power;
                        dao.update(hero);
                        message = getString(R.string.hero_updated, target);
                    } else {
                        dao.delete(hero);
                        message = getString(R.string.hero_deleted, target);
                    }
                }

                List<Hero> heroes = dao.getAll();
                StringBuilder list = new StringBuilder();
                if (!message.isEmpty()) {
                    list.append(message).append('\n');
                }
                list.append(getString(R.string.heroes_total, heroes.size())).append('\n');
                for (Hero hero : heroes) {
                    list.append(hero.id).append(" · ").append(hero.name)
                            .append(" — ").append(hero.power).append('\n');
                }
                ui(() -> binding.result.setText(list));
            } catch (Exception e) {
                ui(() -> binding.result.setText("Ошибка Room: " + e.getMessage()));
            }
        });
    }
}
